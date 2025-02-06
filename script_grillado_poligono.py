# -*- coding: utf-8 -*-
import arcpy
import string
import os

# Parámetros de entrada
multipoligono = arcpy.GetParameterAsText(0)
codigo_poligono = arcpy.GetParameterAsText(1)
tamano_celda = arcpy.GetParameter(2)
porcentaje_interseccion = arcpy.GetParameter(3)
salida_fishnet = arcpy.GetParameterAsText(4)
valor_porcentaje = porcentaje_interseccion / 100

# Permitir sobrescribir archivos de salida
arcpy.env.overwriteOutput = True

try:
    # Validar que el shapefile no esté vacío
    if int(arcpy.management.GetCount(multipoligono)[0]) == 0:
        arcpy.AddError("El shapefile está vacío o no es válido.")
        raise ValueError("El shapefile está vacío o no es válido.")

    # Validar que el tamaño de celda sea mayor que 0
    if tamano_celda <= 0:
        arcpy.AddError("El tamaño de celda debe ser mayor que 0.")
        raise ValueError("El tamaño de celda debe ser mayor que 0.")

    # Obtener la extensión del shapefile
    desc = arcpy.Describe(multipoligono)
    if not hasattr(desc, "extent"):
        arcpy.AddError("No se pudo obtener la extensión del shapefile.")
        raise AttributeError("No se pudo obtener la extensión del shapefile.")

    # Extraer coordenadas de la extensión
    xmin, ymin, xmax, ymax = desc.extent.XMin, desc.extent.YMin, desc.extent.XMax, desc.extent.YMax

    # Crear la grilla (fishnet)
    arcpy.management.CreateFishnet(
        out_feature_class=salida_fishnet,
        origin_coord=f"{xmin} {ymin}",
        y_axis_coord=f"{xmin} {ymin + 10}",
        cell_width=tamano_celda,
        cell_height=tamano_celda,
        number_rows="",
        number_columns="",
        corner_coord=f"{xmax} {ymax}",
        labels="NO_LABELS",
        template=multipoligono,
        geometry_type="POLYGON"
    )

    arcpy.AddMessage(f"✅ Grilla creada correctamente en: {salida_fishnet}")

    # Agregar campos para numeración y área
    arcpy.management.AddField(salida_fishnet, "cod_pol", "TEXT", field_length=10) 
    arcpy.management.AddField(salida_fishnet, "num_fila", "TEXT", field_length=4)
    arcpy.management.AddField(salida_fishnet, "num_colum", "TEXT", field_length=4)
    arcpy.management.AddField(salida_fishnet, "let_colum", "TEXT", field_length=5) 
    arcpy.management.AddField(salida_fishnet, "fila_colum", "TEXT", field_length=10) 
    arcpy.management.AddField(salida_fishnet, "area_inter", "DOUBLE")  
    arcpy.management.AddField(salida_fishnet, "area_gri", "DOUBLE")

    # Función para convertir números en letras (A-ZZ)
    def numero_a_letras(num):
        letras = string.ascii_uppercase
        resultado = ""

        while num >= 0:
            resultado = letras[num % 26] + resultado
            num = num // 26 - 1 

        return resultado

    # Obtener datos de la grilla
    datos_grilla = []
    with arcpy.da.SearchCursor(salida_fishnet, ["OID@", "SHAPE@XY"]) as search_cursor:
        for row in search_cursor:
            datos_grilla.append(row)

    # Ordenar por coordenadas (primero Y, luego X)
    datos_grilla.sort(key=lambda row: (row[1][1], row[1][0]), reverse=True)

    # Obtener valores únicos de Y para numeración de filas
    ys_unicos = sorted(set(y for _, (x, y) in datos_grilla), reverse=True)
    fila_indices = {y: i + 1 for i, y in enumerate(ys_unicos)}

    # Diccionario para contar columnas en cada fila
    col_contadores = {y: 1 for y in ys_unicos}

    # Actualizar los valores de la grilla
    with arcpy.da.UpdateCursor(salida_fishnet, ["OID@", "SHAPE@", "cod_pol", "num_fila", "num_colum", "let_colum", "fila_colum", "area_inter", "area_gri"]) as update_cursor:
        for row in update_cursor:
            oid = row[0]  # ID del objeto
            poligono_celda = row[1]  # Obtenemos el polígono de la celda de la grilla

            fila_actual = fila_indices[poligono_celda.centroid.Y]
            col_actual = col_contadores[poligono_celda.centroid.Y]

            # Obtener la letra de la columna
            col_letra = numero_a_letras(col_actual - 1)

            fila_colum = f"{col_letra}-{fila_actual}"

            # Asignar valores de fila y columna
            row[2] = codigo_poligono
            row[3] = fila_actual 
            row[4] = col_actual
            row[5] = col_letra 
            row[6] = fila_colum  


            intersect_area = 0.0

            # Usar la herramienta de Intersección
            with arcpy.da.SearchCursor(multipoligono, ["SHAPE@"]) as cursor_multipoligono:
                for multipolygon in cursor_multipoligono:
                    intersection = poligono_celda.intersect(multipolygon[0], 4)  # 4 = tipo de intersección: polígonos
                    intersect_area += intersection.area

            intersect_area_hectareas = intersect_area / 10000.0

            # Asignar el área de la intersección
            row[7] = intersect_area_hectareas
            tamano_hectareas = (tamano_celda ** 2) / 10000.0
            row[8] = tamano_hectareas
            update_cursor.updateRow(row)

            col_contadores[poligono_celda.centroid.Y] += 1

    arcpy.AddMessage("✅ Columnas, filas y área de intersección numeradas correctamente.")
    
    # Seleccionar solo las celdas donde el área de intersección sea al menos el 50% del tamaño de la celda
    arcpy.MakeFeatureLayer_management(salida_fishnet, "fishnet_layer")
    sql_expression = f"area_inter >= (area_gri * {valor_porcentaje})"
    arcpy.SelectLayerByAttribute_management("fishnet_layer", "NEW_SELECTION", sql_expression)

    # Guardar las celdas seleccionadas en un archivo temporal y luego sobrescribir la salida original
    temp_output = os.path.join(os.path.dirname(salida_fishnet), "temp_fishnet.shp")
    arcpy.CopyFeatures_management("fishnet_layer", temp_output)

    # Sobrescribir la grilla original con las celdas seleccionadas
    arcpy.management.Delete(salida_fishnet)
    arcpy.management.Rename(temp_output, salida_fishnet)

    arcpy.AddMessage(f"✅ Se sobrescribió la grilla con las celdas seleccionadas en: {salida_fishnet}")

except Exception as e:
    arcpy.AddError(f"❌ Error: {str(e)}")