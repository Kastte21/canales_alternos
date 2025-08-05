import sys
from src.sync.synchronizer import ClienteSynchronizer
from src.sync.envios_synchronizer import EnviosSynchronizer

def mostrar_menu():
    print("\n" + "=" * 60)
    print("MENÚ PRINCIPAL DE SINCRONIZACIÓN")
    print("=" * 60)
    print("1. Sincronizar Clientes (Rápido, con reporte)")
    print("2. Sincronizar Clientes (Modo Auditoría Detallada)")
    print("3. Cargar Envíos desde CONSOLIDADO")
    print("4. Salir")
    print("=" * 60)

def main():
    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción (1-4): ").strip()
        
        try:
            if opcion == "1":
                with ClienteSynchronizer() as sync:
                    sync.run_synchronization(generate_report=True, detailed_output=False)
            
            elif opcion == "2":
                with ClienteSynchronizer() as sync:
                    sync.run_synchronization(generate_report=True, detailed_output=True)
            
            elif opcion == "3":
                with EnviosSynchronizer() as sync:
                    sync.sincronizar_envios()
            
            elif opcion == "4":
                print("\n👋 ¡Hasta luego!")
                sys.exit(0)
            
            else:
                print("\n❌ Opción no válida.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Operación cancelada.")
            sys.exit(0)
        except Exception:
            # Los errores específicos ya se imprimen en las clases
            print("\n❌ La operación falló. Revisa los mensajes de error anteriores.")
        
        input("\nPresione Enter para volver al menú...")

if __name__ == "__main__":
    main()