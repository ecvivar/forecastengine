# PROMPT MAESTRO ENTERPRISE – MOTOR DE SIMULACIÓN COMPLETA DEL MUNDIAL FIFA 2026

Actúa como un departamento profesional de análisis cuantitativo deportivo integrado por:

* Científicos de Datos
* Estadísticos Deportivos
* Analistas de Fútbol Internacional
* Especialistas en Modelos Elo
* Especialistas en xG/xGA
* Modeladores Bayesianos
* Expertos en Simulación Monte Carlo
* Analistas Tácticos
* Analistas de Riesgo e Incertidumbre

Tu objetivo es construir un modelo integral de simulación del Mundial FIFA 2026 que reproduzca una metodología similar a la utilizada por consultoras deportivas profesionales.

NO quiero una predicción simple.

Quiero un modelo de simulación completo del torneo.

Si el volumen de información es excesivo para una única respuesta:

1. Analizar primero todos los grupos.
2. Luego presentar las probabilidades de clasificación.
3. Después generar el cuadro eliminatorio.
4. Finalmente ejecutar la simulación completa del torneo.

Mantener coherencia entre todas las fases utilizando las mismas ponderaciones y parámetros.

---

# GRUPOS OFICIALES – MUNDIAL FIFA 2026

| Grupo | Selecciones                                       |
| ----- | ------------------------------------------------- |
| A     | México, Sudáfrica, Corea del Sur, República Checa |
| B     | Canadá, Bosnia-Herzegovina, Qatar, Suiza          |
| C     | Brasil, Marruecos, Haití, Escocia                 |
| D     | Estados Unidos, Paraguay, Australia, Turquía      |
| E     | Alemania, Curazao, Costa de Marfil, Ecuador       |
| F     | Países Bajos, Japón, Suecia, Túnez                |
| G     | Bélgica, Egipto, Irán, Nueva Zelanda              |
| H     | España, Cabo Verde, Arabia Saudita, Uruguay       |
| I     | Francia, Senegal, Irak, Noruega                   |
| J     | Argentina, Argelia, Austria, Jordania             |
| K     | Portugal, RD Congo, Uzbekistán, Colombia          |
| L     | Inglaterra, Croacia, Ghana, Panamá                |

---

# MÓDULO 1 – RECOLECCIÓN Y VALIDACIÓN DE DATOS

Para cada selección clasificada recopilar y validar:

* Ranking FIFA
* Elo global
* Elo ajustado por competencia
* Últimos 5 partidos
* Últimos 10 partidos
* Últimos 20 partidos
* Rendimiento últimos 24 meses
* Goles a favor
* Goles en contra
* Diferencia de gol
* xG
* xGA
* xGD
* Rendimiento local
* Rendimiento visitante
* Rendimiento neutral
* Rendimiento en torneos oficiales
* Rendimiento en amistosos
* Valor de mercado del plantel
* Edad promedio
* Experiencia internacional
* Experiencia mundialista
* Lesiones
* Suspensiones
* Convocatorias oficiales

Validar consistencia de datos.

Diferenciar explícitamente:

* Datos observados.
* Datos estimados.
* Datos imputados.

Asignar nivel de confianza a cada fuente.

---

# MÓDULO 2 – CONSTRUCCIÓN DEL ÍNDICE GLOBAL DE FUERZA (IGF)

Crear un modelo de rating compuesto.

Ponderación inicial:

* Elo Ajustado = 25%
* Forma Reciente = 20%
* xG/xGA = 20%
* Fortaleza de Rivales = 10%
* Experiencia Mundialista = 10%
* Calidad del Plantel = 10%
* Historial Reciente en Torneos = 5%

Generar:

* IGF (0-100)

Para todas las selecciones.

Mostrar ranking completo.

Justificar cualquier modificación de ponderaciones.

---

# MÓDULO 3 – ANÁLISIS DE GRUPOS

Para cada grupo:

* Ranking interno.
* Diferencias de fuerza.
* Favoritos.
* Outsiders.
* Riesgo de sorpresa.
* Índice de competitividad del grupo.
* Distancia entre primero y último según IGF.

Generar análisis comparativo.

---

# MÓDULO 4 – MODELADO DE PARTIDOS

Para TODOS los partidos de la fase de grupos:

Calcular:

* Elo diferencial.
* xG esperado.
* xGA esperado.
* Ajuste de forma.
* Ajuste de localía.
* Ajuste de descanso.
* Ajuste de calidad de rival.

Calcular:

* Lambda Equipo A
* Lambda Equipo B

Aplicar:

* Poisson
* Dixon-Coles
* Ajustes Bayesianos

Generar:

* Victoria Equipo A
* Empate
* Victoria Equipo B
* Top 10 marcadores probables

Mostrar fórmulas utilizadas.

---

# MÓDULO 4B – PROYECCIÓN DE RESULTADOS INDIVIDUALES

Para cada partido de la fase de grupos calcular:

### Goles Esperados

* xG Equipo A
* xG Equipo B
* Lambda Equipo A
* Lambda Equipo B

### Marcador Modal

Identificar el marcador individual con mayor probabilidad.

Ejemplo:

Argentina 2 – 0 Jordania

Probabilidad: 14,2%

### Top 10 Resultados Más Probables

Mostrar:

| Ranking | Resultado | Probabilidad |
| ------- | --------- | ------------ |
| 1       | 2-0       | xx%          |
| 2       | 1-0       | xx%          |
| 3       | 2-1       | xx%          |

### Marcador Esperado

Resultado promedio derivado de las lambdas.

### Índice de Confianza

Escala 0–100.

Considerar:

* Diferencia Elo
* Diferencia IGF
* Volatilidad histórica
* Varianza de resultados

Clasificación:

* 80-100 = Muy Alta
* 65-79 = Alta
* 50-64 = Media
* 35-49 = Baja
* 0-34 = Muy Baja

### Riesgo de Sorpresa

Calcular:

Probabilidad de que el no favorito obtenga puntos.

---

# MÓDULO 5 – SIMULACIÓN DE FASE DE GRUPOS

Ejecutar mínimo:

100.000 simulaciones completas.

Para cada simulación:

* Jugar todos los partidos.
* Asignar puntos.
* Aplicar reglamento FIFA.
* Construir tabla final.

Generar probabilidad de:

* Terminar 1°
* Terminar 2°
* Terminar 3°
* Terminar 4°

para cada selección.

---

# MÓDULO 5B – CALENDARIO PROYECTADO COMPLETO DE LA FASE DE GRUPOS

Antes de ejecutar las simulaciones Monte Carlo:

Generar los 72 partidos oficiales de la fase de grupos.

Para cada encuentro mostrar:

| Partido                          | Marcador Más Probable | Probabilidad | Confianza |
| -------------------------------- | --------------------- | ------------ | --------- |
| México vs Sudáfrica              | X-X                   | XX%          | XX        |
| Corea del Sur vs República Checa | X-X                   | XX%          | XX        |

Mostrar los 72 partidos.

---

# MÓDULO 5C – TABLA PROYECTADA DE CADA GRUPO

Utilizando los marcadores modales:

Generar una tabla preliminar proyectada.

Mostrar:

* PJ
* PG
* PE
* PP
* GF
* GC
* DG
* PTS

Aclarar que esta tabla corresponde al escenario modal y no a la simulación Monte Carlo.

---

# MÓDULO 6 – CLASIFICACIÓN A ELIMINATORIAS

Calcular probabilidad de:

* Clasificación directa.
* Clasificación como mejor tercero.
* Eliminación.

Para cada selección.

---

# MÓDULO 7 – GENERACIÓN AUTOMÁTICA DEL CUADRO

Construir automáticamente:

* Dieciseisavos
* Octavos
* Cuartos
* Semifinales
* Final

Siguiendo el reglamento oficial FIFA 2026.

Mostrar todos los cruces posibles.

Mostrar también el cuadro más probable.

---

# MÓDULO 8 – SIMULACIÓN DEL TORNEO COMPLETO

Ejecutar:

100.000 simulaciones completas.

En cada simulación:

1. Simular grupos.
2. Clasificar equipos.
3. Construir cuadro.
4. Simular eliminatorias.
5. Determinar campeón.

Registrar resultados.

---

# MÓDULO 8B – RESULTADOS MÁS FRECUENTES DEL TORNEO

Informar:

* Campeón más frecuente.
* Final más frecuente.
* Semifinales más frecuentes.
* Cuartos de final más frecuentes.
* Eliminaciones sorpresivas más frecuentes.
* Grupos con mayor volatilidad.
* Grupos con menor volatilidad.

---

# MÓDULO 9 – PROBABILIDADES POR RONDA

Para cada selección calcular probabilidad de alcanzar:

* Dieciseisavos
* Octavos
* Cuartos
* Semifinales
* Final
* Campeón

Mostrar tabla completa.

---

# MÓDULO 9B – PROBABILIDADES DE PARTIDO

Para cada encuentro informar:

* Victoria Equipo A
* Empate
* Victoria Equipo B
* Ambos equipos marcan
* Over 2.5 goles
* Under 2.5 goles
* Over 3.5 goles
* Portería a cero Equipo A
* Portería a cero Equipo B

---

# MÓDULO 10 – ANÁLISIS DE SENSIBILIDAD

Evaluar impacto de:

* Lesiones de figuras.
* Cambios de convocatoria.
* Forma reciente.
* Localía.
* Fatiga.
* Viajes.
* Clima.
* Altitud.

Determinar variables más influyentes.

---

# MÓDULO 10B – INCERTIDUMBRE DE PLANTEL

Modelar escenarios probabilísticos para:

* Lesiones de jugadores clave.
* Suspensiones.
* Rotaciones.
* Cambios tácticos.

Generar:

* Escenario Base.
* Escenario Optimista.
* Escenario Pesimista.

Recalcular probabilidades del torneo para cada escenario.

---

# MÓDULO 11 – ESCENARIOS

Construir:

* Escenario Conservador.
* Escenario Base.
* Escenario Optimista.
* Escenario Sorpresa.
* Escenario Caótico.

Explicar probabilidades y detonantes.

---

# MÓDULO 11B – CALIBRACIÓN HISTÓRICA

Validar el modelo utilizando:

* Mundial 2014
* Mundial 2018
* Mundial 2022

Comparar:

* Probabilidades estimadas.
* Resultados reales.
* Precisión de clasificación.
* Precisión de campeón.
* Precisión de semifinalistas.

Calcular:

* Brier Score.
* Log Loss.
* Accuracy.
* Calibration Error.

Ajustar ponderaciones si se detectan sesgos sistemáticos.

---

# MÓDULO 12 – VALIDACIÓN DEL MODELO

Comparar resultados con:

* Elo.
* Ranking FIFA.
* Modelos públicos.
* Casas de análisis deportivas.

Identificar coincidencias y divergencias.

---

# MÓDULO 13 – POWER RANKING DEL TORNEO

Generar:

* Top 10 candidatos al título.
* Top 10 candidatos a semifinales.
* Top 10 candidatos a cuartos.
* Top 10 candidatos a eliminación temprana.

---

# MÓDULO 14 – INFORME EJECUTIVO FINAL

Presentar:

1. Favorito principal al título.
2. Top 5 favoritos.
3. Probabilidad de campeón de cada selección.
4. Grupos más competitivos.
5. Grupos más previsibles.
6. Principales sorpresas potenciales.
7. Selección más sobrevalorada.
8. Selección más subvalorada.
9. Riesgos del modelo.
10. Conclusiones finales.

---

# MÓDULO 14B – ÍNDICE DE CONFIANZA

Asignar una puntuación de confianza entre 0 y 100.

Considerar:

* Calidad de los datos disponibles.
* Cantidad de partidos recientes.
* Consistencia histórica.
* Volatilidad de resultados.
* Incertidumbre de planteles.

Clasificación:

* 90-100 = Muy Alta
* 75-89 = Alta
* 60-74 = Moderada
* 40-59 = Baja
* 0-39 = Muy Baja

---

# MÓDULO 14C – INFORME EJECUTIVO DE MARCADORES

Presentar:

* Los 20 partidos más desequilibrados.
* Los 20 partidos más parejos.
* Mayor probabilidad de goleada.
* Mayor probabilidad de empate.
* Partido con mayor incertidumbre.
* Partido con mayor expectativa de goles.
* Partido con menor expectativa de goles.

---

# AUDITORÍA INTERNA OBLIGATORIA

Antes de generar conclusiones:

Identificar y cuantificar:

* Posibles sesgos del modelo.
* Dependencia excesiva del Elo.
* Dependencia excesiva del xG.
* Overfitting.
* Muestras insuficientes.
* Variables altamente correlacionadas.
* Equipos con elevada incertidumbre estadística.

Proponer correcciones si fueran necesarias.

---

# REGLAS OBLIGATORIAS

* Utilizar datos verificables y actualizados.
* Diferenciar hechos de estimaciones.
* Mostrar fórmulas utilizadas.
* Justificar ponderaciones.
* Cuantificar incertidumbre.
* Mostrar intervalos de confianza.
* Explicar limitaciones.
* Priorizar rigor estadístico sobre narrativa.
* Pensar como un departamento profesional de forecasting deportivo.
* Si existen datos insuficientes para una variable, estimarla explícitamente e indicar el nivel de confianza.

## REGLA ADICIONAL CRÍTICA

Para cada uno de los 72 partidos de la fase de grupos el modelo deberá informar explícitamente:

* Probabilidad de victoria de cada equipo.
* Probabilidad de empate.
* Marcador modal.
* Top 10 marcadores más probables.
* Goles esperados de ambos equipos.
* Índice de confianza.
* Riesgo de sorpresa.

No se permite limitar el análisis únicamente a probabilidades de clasificación o posiciones finales.

Cada partido deberá contar con una proyección específica de resultado antes de ejecutar las simulaciones completas del torneo.
