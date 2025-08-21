
import arcpy
import string
import os

multipoligono = arcpy.GetParameterAsText(0)
codigo_poligono = arcpy.GetParameterAsText(1)
celda_width = arcpy.GetParameter(2)
celda_height = arcpy.GetParameter(3)
porcentaje_interseccion = arcpy.GetParameter(4)
salida_fishnet = arcpy.GetParameterAsText(5)
valor_porcentaje = porcentaje_interseccion / 100
arcpy.env.overwriteOutput = True

# Función para convertir números en letras (A-ZZ)
def numero_a_letras(num):
    letras = string.ascii_uppercase
    resultado = ""

    while num >= 0:
        resultado = letras[num % 26] + resultado
        num = num // 26 - 1 

    return resultado

try:
    #Calcular extensión
    extent = None

    with arcpy.da.SearchCursor(multipoligono, ["SHAPE@"]) as cursor:
        for row in cursor:
            if extent is None:
                extent = row[0].extent
            else:
                extent = arcpy.Extent(
                min(extent.XMin, row[0].extent.XMin),
                min(extent.YMin, row[0].extent.YMin),
                max(extent.XMax, row[0].extent.XMax),
                max(extent.YMax, row[0].extent.YMax)
            )

    # Extraer coordenadas de la extensión
    xmin, ymin, xmax, ymax = extent.XMin, extent.YMin, extent.XMax, extent.YMax

    # Crear la grilla (fishnet)
    arcpy.management.CreateFishnet(
        out_feature_class=salida_fishnet,
        origin_coord=f"{xmin} {ymin}",
        y_axis_coord=f"{xmin} {ymin + 10}",
        cell_width=celda_width,
        cell_height=celda_height,
        number_rows="",
        number_columns="",
        corner_coord=f"{xmax} {ymax}",
        labels="NO_LABELS",
        template=multipoligono,
        geometry_type="POLYGON"
    )

    # Agregar campos para numeración y área
    arcpy.management.AddField(salida_fishnet, "poly_code", "TEXT", field_length=10) 
    arcpy.management.AddField(salida_fishnet, "row_num", "TEXT", field_length=4)
    arcpy.management.AddField(salida_fishnet, "col_num", "TEXT", field_length=4)
    arcpy.management.AddField(salida_fishnet, "col_let", "TEXT", field_length=5) 
    arcpy.management.AddField(salida_fishnet, "rowcol_id", "TEXT", field_length=10) 
    arcpy.management.AddField(salida_fishnet, "int_area", "DOUBLE")  
    arcpy.management.AddField(salida_fishnet, "grid_area", "DOUBLE")
    arcpy.management.DeleteField(salida_fishnet, ["Id"])

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
    col_contadores = {y: 1 for y in ys_unicos}

    # Actualizar los valores de la grilla
    with arcpy.da.UpdateCursor(salida_fishnet, ["OID@", "SHAPE@", "poly_code", "row_num", "col_num", "col_let", "rowcol_id", "int_area", "grid_area"]) as update_cursor:
        for row in update_cursor:
            oid = row[0]  
            poligono_celda = row[1] 
            fila_actual = fila_indices[poligono_celda.centroid.Y]
            col_actual = col_contadores[poligono_celda.centroid.Y]
            col_letra = numero_a_letras(col_actual - 1)
            fila_colum = f"{col_letra}-{fila_actual}"
            row[2] = codigo_poligono
            row[3] = fila_actual 
            row[4] = col_actual
            row[5] = col_letra 
            row[6] = fila_colum  
            intersect_area = 0.0

            # Usar la herramienta de Intersección
            with arcpy.da.SearchCursor(multipoligono, ["SHAPE@"]) as cursor_multipoligono:
                for multipolygon in cursor_multipoligono:
                    intersection = poligono_celda.intersect(multipolygon[0], 4)
                    intersect_area += intersection.area


            # Asignar el área de la intersección
            row[7] = intersect_area
            area_grilla = (celda_height * celda_width) 
            row[8] = area_grilla
            update_cursor.updateRow(row)

            col_contadores[poligono_celda.centroid.Y] += 1

    arcpy.AddMessage("✅ Columnas, filas numeradas correctamente.")
    
    # Seleccionar solo las celdas donde el área de intersección sea al menos el porcentaje indicado en el parametro
    arcpy.MakeFeatureLayer_management(salida_fishnet, "fishnet_layer")
    sql_expression = f"int_area >= (grid_area * {valor_porcentaje})"
    arcpy.SelectLayerByAttribute_management("fishnet_layer", "NEW_SELECTION", sql_expression)

    # Guardar las celdas seleccionadas en un archivo temporal y luego sobrescribir la salida original
    temp_output = os.path.join(os.path.dirname(salida_fishnet), "temp_fishnet.shp")
    arcpy.CopyFeatures_management("fishnet_layer", temp_output)
    arcpy.management.Delete(salida_fishnet)
    arcpy.management.Rename(temp_output, salida_fishnet)

    arcpy.AddMessage(f"✅ Grillado generado correctamente: {salida_fishnet}")

except Exception as e:
    arcpy.AddError(f"❌ Error: {str(e)}")

