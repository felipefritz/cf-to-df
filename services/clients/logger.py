import logging
import colorlog

def get_logger():
    # Obtener el nombre del módulo actual (sin el .py)
    module_name = __name__.split(".")[-1]

    # Configurar el registro de logs para el módulo actual
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)  # Puedes ajustar el nivel según tus necesidades

    # Definir un esquema de colores para los mensajes de log
    log_colors = {
        'DEBUG': 'cyan',
        'INFO': 'white',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }

    # Crear un formateador de colores
    formatter = colorlog.ColoredFormatter(
        '%(asctime)s - %(name)s - %(log_color)s%(levelname)s - %(message)s',
        log_colors=log_colors
    )

    # Agregar un manejador de logs para imprimir los mensajes en la consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
