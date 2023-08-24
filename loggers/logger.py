import logging
import colorlog
import os

def get_logger(log_type="info"):
    # Obtener el nombre del módulo actual (sin el .py)
    module_name = __name__.split(".")[-1]

    # Configurar el registro de logs para el módulo actual
    logger = logging.getLogger(module_name)
    logger.setLevel(getattr(logging, log_type.upper()))

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(module)s - line (%(lineno)d) - %(levelname)s - %(message)s')

    # Agregar un manejador de logs para guardar los mensajes en un archivo
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_file = f"{log_directory}/{log_type}.log"
    
    # Comprobar si el logger ya tiene un FileHandler para este tipo de log y, en caso afirmativo, eliminarlo
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == os.path.abspath(log_file):
            logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, log_type.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


