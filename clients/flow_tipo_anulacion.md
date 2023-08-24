Páginas (Pages) y Subpáginas (Subpages) con sus respectivos Entity Types:

## Página Principal (TipoAnulacionPage):
Pregunta: "Cuéntame, ¿Qué tipo de anulación quieres hacer?"
Entity Type: tipo-información-anular-pago
Chips:
"Eliminar pago automático" (Redirige a EliminarPagoAutomaticoPage)
"Reversar pago" (Redirige a ReversarPagoPage)


## Subpágina (EliminarPagoAutomaticoPage):
Pregunta: "¿Que tipo de pago de servicio deseas eliminar?"
Entity Type: pagosautomaticos
Chips:
"PAC" (URL: intent://faq.eliminarpac.info)
"PAT" (URL: intent://faq.eliminarpat.info)


## Subpágina (ReversarPagoPage):
Pregunta: "Cuéntame, ¿Qué tipo de pago quieres reversar?"
Entity Type: producto-pago
Chips:
"Crédito de consumo" (URL: intent://faq.pasolineadigital.info)
"Crédito Hipotecario" (URL: intent://faq.pasolineadigital.info)
... (otros productos de pago)
Rutas de Transición (Transition Routes) basadas en la clave location:

Desde TipoAnulacionPage, si el usuario selecciona el chip "Eliminar pago automático", transición a EliminarPagoAutomaticoPage.
Desde TipoAnulacionPage, si el usuario selecciona el chip "Reversar pago", transición a ReversarPagoPage.
Entry Fulfillment en función de los chips y la clave location:

En TipoAnulacionPage, al mostrar los chips, debes programar la funcionalidad para que, al seleccionar uno, redirija al usuario a la ubicación (subpágina) correspondiente.
Similarmente, en las subpáginas como EliminarPagoAutomaticoPage y ReversarPagoPage, al seleccionar un chip, se debe redirigir al usuario al URL correspondiente o hacer la acción requerida.




flujo de payload responses:

Crear Intents:
Debes crear un intent para cada opción que presentes en el custom payload. En este caso, tendrías un intent para "Rojo" y otro para "Azul". Asegúrate de que cada intent pueda reconocer no solo el título del botón (por ejemplo, "Rojo") sino también el payload (por ejemplo, "COLOR_ROJO"). Esto es útil porque algunos usuarios podrían hacer clic en el botón, mientras que otros podrían escribir su respuesta.

Manejar la Respuesta:
Una vez que el usuario hace clic en un botón o responde, su respuesta (ya sea el título del botón o el payload) activará el intent correspondiente. Utilizando las transition routes en tu página, puedes definir qué hacer cuando se activa un intent específico.

Capturar como Parámetro (opcional):
Si deseas guardar la selección del usuario para usarla más tarde, puedes definir un parámetro en tu página y, en la configuración del intent, asegurarte de que la respuesta del usuario se asigna a ese parámetro.

Así es como puedes capturar y manejar la respuesta del usuario desde un custom payload. Es esencial planificar y diseñar tus intents y transiciones adecuadamente para garantizar que la conversación fluya de manera natural y sin errores.


Start Page
│
└── Menú Principal
    ├── Subflujo 1 (Página Padre)
    │   ├── Página Hijo 1.1
    │   ├── Página Hijo 1.2
    │   └── ...
    │
    ├── Subflujo 2 (Página Padre)
    │   ├── Página Hijo 2.1
    │   └── ...
    │
    └── ...




