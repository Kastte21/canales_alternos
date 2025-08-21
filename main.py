# main.py
import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

try:
    from app.logic import client_synchronizer, send_synchronizer, campaign_synchronizer, mail_synchronizer
except ImportError as e:
    logging.error(f"Error al importar módulos de la aplicación: {e}")
    logging.error("Asegúrate de que la estructura del proyecto y los archivos __init__.py son correctos.")
    sys.exit(1)

def show_menu():
    """Muestra el menú principal de la aplicación."""
    print("\n" + "=" * 60)
    print("                       MENÚ PRINCIPAL ")
    print("=" * 60)
    print(" 1. Cargar Clientes (Rápido, con reporte)")
    print(" 2. Cargar Clientes (Modo Auditoría Detallada)")
    print(" 3. Cargar Envíos desde CONSOLIDADO")
    print(" 4. Cargar Campaña (Reemplazo Mensual)")
    print(" 5. Cargar Mails Información Adicional (Reemplazo Mensual)")
    print(" 6. Salir")
    print("=" * 60)

def main():
    """Bucle principal de la aplicación."""
    while True:
        show_menu()
        option = input("Seleccione una opción (1-6): ").strip()
        
        start_time = datetime.now()
        process_executed = False
        try:
            if option == "1":
                client_synchronizer.run_client_synchronization(generate_report=True, detailed_output=False)
                process_executed = True
            
            elif option == "2":
                client_synchronizer.run_client_synchronization(generate_report=True, detailed_output=True)
                process_executed = True
            
            elif option == "3":
                send_synchronizer.run_send_synchronization()
                process_executed = True

            elif option == "4":
                confirm = input("⚠️  Esta operación borrará TODAS las campañas existentes. ¿Desea continuar? (s/n): ").lower()
                if confirm == 's':
                    campaign_synchronizer.run_campaign_synchronization()
                    process_executed = True
                else:
                    logging.info("Operación de carga de campaña cancelada por el usuario.")
            
            elif option == "5":
                confirm = input("⚠️  Esta operación borrará TODOS los mails existentes. ¿Desea continuar? (s/n): ").lower()
                if confirm == 's':
                    mail_synchronizer.run_mail_synchronization()
                    process_executed = True
                else:
                    logging.info("Operación de carga de mails cancelada por el usuario.")
            
            elif option == "6":
                print("\n👋 ¡Hasta luego!")
                sys.exit(0)
            
            else:
                logging.warning("Opción no válida. Por favor, intente de nuevo.")
        
        except KeyboardInterrupt:
            logging.warning("\nOperación cancelada por el usuario.")
            sys.exit(0)
        except Exception:
            logging.error(f"La operación falló. Revisa los mensajes de error anteriores.")
        
        if process_executed:
            duration = datetime.now() - start_time
            logging.info(f"Duración total de la operación: {duration}")
        
        input("\nPresione Enter para volver al menú...")

if __name__ == "__main__":
    main()