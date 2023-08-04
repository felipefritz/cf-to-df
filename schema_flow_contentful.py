flow_with_chips =  {
  "question": "Quiero conocer como hacer una solicitud o reclamo, o cómo consultar su estado.",
  "startNode": {
    "text": "¿Sobre qué tipo de solicitud quieres consultar?",
    "entityType": {
      "entityType": "requirements-and-claims-type",
      "entityValue": [
        {
          "entityValue": "Requerimientos",
          "synonyms": ["Requerimientos", "Solicitud", "Abrir caso"]
        },
        {
          "entityValue": "Reclamos",
          "synonyms": ["Reclamos", "Reclamar"]
        },
        {
          "entityValue": "Cambio de sucrsal",
          "synonyms": ["Cambio de sucursal", "Cambar sucursal"]
        }
      ]
    },
    "chips": [
      {
        "text": "Requerimientos",
        "location": {
          "text": "¿Qué quieres hacer respecto a tus requerimientos?",
          "buttons": [
            {
              "text": "Ingresar requerimiento",
              "url": "faq.reqingresar.info"
            },
            {
              "text": "Seguimiento",
              "url": "faq.reqseguimiento.info"
            }
          ],
          "fallbacks": [
            {
              "text": "No entendí eso. Elige una de las opciones enumeradas o haz una nueva pregunta."
            }
          ]
        },
        "entityValue": {
          "entityValue": "Requerimientos",
          "synonyms": ["Requerimientos", "Solicitud", "Abrir caso"]
        },
        "forgetParameter": False
      },
      {
        "text": "Reclamos",
        "location": {
          "text": "¿Qué quieres hacer respecto a tus reclamos?",
          "buttons": [
            {
              "text": "Ingresar Reclamo",
              "url": "faq.reclamoingresar.info"
            },
            {
              "text": "Seguimiento",
              "url": "faq.reclamoseguimiento.info"
            }
          ],
          "fallbacks": [
            {
              "text": "No entendí eso. Elige una de las opciones enumeradas o haz una nueva pregunta."
            }
          ]
        },
        "entityValue": {
          "entityValue": "Reclamos",
          "synonyms": ["Reclamos", "Reclamar"]
        },
        "forgetParameter": False
      },
      {
        "text": "Cambio de sucursal",
        "url": "intent://faq.reqyreclamoscambiosuc.info",
        "entityValue": {
          "entityValue": "Cambio de sucursal",
          "synonyms": ["Cambio de sucursal", "Cambar sucursal"]
        },
        "forgetParameter": False
      }
    ],
    "fallbacks": [
      {
        "text": "No entendí eso. Elige una de las opciones enumeradas o haz una nueva pregunta."
      }
    ]
  },
  "intent": "flow.reqyreclamos.info"
}


schema_2 = {
   "text":"Aquí encontrarás nuestros programas de Lealtad.",
   "entityType":{
      "entityType":"programas-lealtad-tipos",
      "entityValue":[
         {
            "entityValue":"Scotia Puntos"
         },
         {
            "entityValue":"Millas"
         }
      ]
   },
   "chips":[
      {
         "text":"Scotia Puntos",
         "location":{
            "text":"Puedes canjear productos o servicios en los establecimientos afiliados, acumulando puntos por el uso de tus tarjetas de débito y crédito Scotiabank.",
            "list":[
               {
                  "text":"Acumulo Puntos",
                  "url":"intent://flow.lealtad.acumular"
               },
               {
                  "text":"Canjea Puntos",
                  "url":"intent://flow.lealtad.canjear"
               }
            ]
         },
         "entityValue":{
            "entityValue":"Scotia Puntos"
         },
         "forgetParameter":False
      },
      {
         "text":"Millas",
         "location":{
            "text":"Acumula millas por el uso de tus Tarjetas de Crédito Scotiabank AAdvantage®, las cuales puedes canjear en viajes, upgrades, etc.",
            "list":[
               {
                  "text":"Acumulo Puntos",
                  "url":"intent://flow.lealtad.acumular"
               },
               {
                  "text":"Canjea Millas",
                  "url":"intent://flow.lealtad.canjear"
               }
            ]
         },
         "entityValue":{
            "entityValue":"Millas"
         },
         "forgetParameter": False
      }
   ],
   "fallbacks":[
      {
         "text":"No entendí eso. Elige una de las opciones enumeradas o haz una nueva pregunta."
      }
   ]
}