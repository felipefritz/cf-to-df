1. Desde el default flow en default start page agregar un route group
2. en el route group deben estar las rutas que haran la transicion a otro flow
3. las route de route groups deben tener un intent que viene de mi data
4. La ruta asociada a un intent debe tener una transicion de tipo flow a un flow especifico

en flow hijo:
1.  El start page del flow hijo debe tener la route group de la cual se hizo la transicion con una route pero que transicione hacia un custom startpage a traves el intent de la route
2. la pagina custom startpage debe tener un entry fullfilment con 2 mensajes de entrada, uno es un "hola que quieres activar" o lo que venga en la data, el segundo debe ser un custom payload con opciones para seleccionar que serian los chips
3. la custom start page debe teneter ademas parameters que serian los entity types
4. debe tener ademas una route con conditions: $session.params.nombre-entity-type: value: entity type value, puede tener muchos sesion params con entity types
5. la transition de la route de la page es a una subpage




1. Desde el default flow en default start page agregar un route group:
python
Copy code
def add_route_group_to_start_page(self, start_page):
    # Asegúrate de que la lista de state_handlers esté inicializada
    if not start_page.state_handlers:
        start_page.state_handlers = []
    # Agregar un nuevo State Handler (Route Group)
    state_handler = dialogflowcx.StateHandler()
    start_page.state_handlers.append(state_handler)
    return self.pages_manager.update_page(start_page)
2. En el route group deben estar las rutas que harán la transición a otro flow:
python
Copy code
def add_transition_route_to_state_handler(self, start_page, intent, target_flow):
    transition_route = dialogflowcx.TransitionRoute()
    transition_route.intent = intent
    transition_route.target_flow = target_flow
    # Asumiendo que el último State Handler es el que agregaste anteriormente
    start_page.state_handlers[-1].transition_routes.append(transition_route)
    return self.pages_manager.update_page(start_page)
3. Las route de route groups deben tener un intent que viene de mi data:
Esto ya está cubierto en el método anterior con el parámetro intent.

4. La ruta asociada a un intent debe tener una transición de tipo flow a un flow específico:
Esto también está cubierto en el método anterior con el parámetro target_flow.

En el flujo hijo:
1. El start page del flow hijo debe tener la route group de la cual se hizo la transición con una route pero que transicione hacia un custom startpage a través del intent de la route:
Puedes reutilizar el método add_route_group_to_start_page y add_transition_route_to_state_handler para lograr esto, pero asegúrate de que el target sea la custom start page.

2. La página custom startpage debe tener un entry fulfillment con 2 mensajes de entrada:
python
Copy code
def add_entry_fulfillment_to_page(self, custom_start_page, messages):
    fulfillment = dialogflowcx.Fulfillment(messages=messages)
    custom_start_page.entry_fulfillment = fulfillment
    return self.pages_manager.update_page(custom_start_page)
3. La custom start page debe tener además parameters que serían los entity types:
python
Copy code
def add_parameters_to_page(self, custom_start_page, parameters):
    custom_start_page.parameters.extend(parameters)
    return self.pages_manager.update_page(custom_start_page)
4. Debe tener además una route con conditions:
python
Copy code



# parametros
$session.params.param1 == "value1" && $session.params.param2 != "value2"

$session.params.nombre-entity-type == "example_value"
Así que, cuando uses el método add_condition_route_to_page, puedes pasar una condición como esta:

python
Copy code
condition = "$session.params.nombre-entity-type == 'example_value'"
self.add_condition_route_to_page(custom_start_page, condition, transition_to
def add_condition_route_to_page(self, custom_start_page, condition, transition):
    route = dialogflowcx.TransitionRoute(condition=condition, transition=transition)
    custom_start_page.transition_routes.append(route)
    return self.pages_manager.update_page(custom_start_page)


En Dialogflow CX, los parámetros juegan un papel crucial en la gestión de la información a lo largo de una conversación. Existen dos tipos principales de parámetros: parámetros de página y parámetros de sesión. Aquí te explico la diferencia entre ambos:

## Parámetros de Página:

Estos parámetros son específicos de una página en particular.
Se utilizan principalmente para extraer y almacenar información de las entradas del usuario dentro del contexto de una página específica.
Por ejemplo, si tienes una página donde esperas que el usuario proporcione su nombre, puedes tener un parámetro de página llamado "nombre" que capture y almacene esa información.
Estos parámetros no persisten entre diferentes páginas. Una vez que la conversación se mueve a una página diferente, los parámetros de la página anterior ya no están directamente accesibles.

## Parámetros de Sesión ($session.params):

Estos parámetros persisten durante toda la conversación, independientemente de las transiciones de página.
Son útiles para almacenar información que necesita ser accesible o referenciada en múltiples puntos a lo largo de la conversación.
Por ejemplo, si capturas el nombre del usuario al principio de la conversación y deseas referenciarlo en varias páginas o flujos diferentes, puedes almacenar esa información en un parámetro de sesión.
Las condiciones de las rutas de transición a menudo hacen referencia a estos parámetros para determinar cómo debe proceder la conversación.
Ejemplo:
Supongamos que tienes una conversación donde primero preguntas el nombre del usuario y luego su edad.

En la página "PreguntaNombre", podrías tener un parámetro de página llamado "nombreTemporal" que captura el nombre del usuario.
Una vez que el usuario proporciona su nombre, puedes establecer un parámetro de sesión llamado "nombreUsuario" con el valor de "nombreTemporal".
Luego, en una página posterior, "PreguntaEdad", incluso si tienes otros parámetros de página para capturar la edad, aún puedes acceder al "nombreUsuario" desde $session.params.nombreUsuario para, por ejemplo, decir "Gracias, [nombreUsuario]. Ahora, ¿cuántos años tienes?".
En resumen, mientras que los parámetros de página son específicos y temporales a una página, los parámetros de sesión son persistentes y accesibles a lo largo de toda la conversación. Es una buena práctica utilizar parámetros de sesión para información que se espera que sea relevante en múltiples puntos de la conversación.


def add_transition_routes_based_on_session_params(self, custom_start_page, session_param_name, transitions):
    """Agrega rutas de transición basadas en valores de parámetros de sesión.

    Args:
        custom_start_page (Page): La página a la que se agregarán las rutas de transición.
        session_param_name (str): El nombre del parámetro de sesión a verificar.
        transitions (dict): Un diccionario que mapea valores de parámetros a nombres de páginas de destino.

    Returns:
        Page: La página actualizada con las nuevas rutas de transición.
    """
    for value, target_page in transitions.items():
        condition = f"$session.params.{session_param_name} == '{value}'"
        transition_route = dialogflowcx.TransitionRoute(condition=condition, target_page=target_page)
        custom_start_page.transition_routes.append(transition_route)
    return self.pages_manager.update_page(custom_start_page)
Uso:
python
Copy code
# Definir las transiciones basadas en valores de parámetros
transitions = {
    "tarjeta de crédito": "projects/your_project_id/locations/your_location/agents/your_agent_id/pages/activacion.tarjetadecredito",
    "tarjeta de débito": "projects/your_project_id/locations/your_location/agents/your_agent_id/pages/activacion.tarjetadedebito"
}

# Agregar rutas de transición a la "Custom Start Page"
self.add_transition_routes_based_on_session_params(custom_start_page, "tipo-activacion", transitions)
Con este enfoque, cuando el usuario proporciona un tipo de activación (por ejemplo, "tarjeta de crédito"), la conversación transicionará automáticamente a la página correspondiente, en este caso, "activacion.tarjetadecredito".




