# 🗺️ Herramienta Fishnet con cálculo de porcentaje de área

Herramienta desarrollada en **Python 3.11** utilizando la librería **ArcPy** para **ArcGIS Pro**, que permite generar **grillas (fishnet)** sobre un polígono de entrada.  

Cada celda es **codificada mediante un sistema alfanumérico (números y letras)** y se calcula el **porcentaje de intersección entre la celda y el polígono**, lo que facilita analizar la cobertura espacial de la grilla respecto al área de estudio.  

El resultado se exporta como **shapefile o feature class** y se añade automáticamente al proyecto de ArcGIS Pro para su visualización.



---


## 📌 Flujo de uso

### 1. Ingreso de parámetros
- **Polígono de entrada**: Shapefile o Feature Class que delimita el área de análisis.  
- **Código del polígono**: Identificador único que se asignará a las celdas generadas.  
- **Ancho y alto de celda**: Dimensiones (en metros) para construir cada unidad de la grilla.  
- **Porcentaje mínimo de intersección**: Umbral (%) para conservar únicamente las celdas que cumplen con la superposición mínima.  
- **Ruta de salida**: Carpeta o Geodatabase donde se guardará la grilla final.  

### 2. Generación de la grilla
- Se crea un **fishnet regular** que cubre la extensión del polígono.  
- Cada celda recibe un **código alfanumérico único (letra + número)** para su identificación.  

### 3. Cálculo de intersección
- Se evalúa el **área de superposición de cada celda con el polígono**.  
- Se asigna en la tabla de atributos el **porcentaje de intersección**.  
- Solo permanecen las celdas que cumplen con el umbral definido.  

### 4. Exportación y visualización
- El resultado se guarda como **shapefile o feature class**.  
- La capa se agrega automáticamente al **contenido del proyecto de ArcGIS Pro**.  

---

## 📷 Vista previa de resultados

<p align="center">
  <img src="https://github.com/user-attachments/assets/6df46dce-7303-4fc4-9a86-31c668445f0f" alt="Vista previa de la grilla generada en ArcGIS Pro" width="600"/>
</p>

<p align="center"><i>Figura: Ejemplo de grilla generada y codificada sobre un polígono en ArcGIS Pro</i></p>
