#!/usr/bin/env python3
"""
Script principal para sincronización de clientes
Permite elegir entre diferentes tipos de sincronización
"""

import sys
from src.sync.synchronizer import ClienteSynchronizer
from src.sync.envios_synchronizer import EnviosSynchronizer

def mostrar_menu():
    print("=" * 60)
    print("SINCRONIZACIÓN DE CLIENTES Y ENVÍOS")
    print("=" * 60)
    print("1. Sincronización Detallada (análisis y auditoría)")
    print("2. Sincronización Simplificada (carga rápida)")
    print("3. Sincronización Optimizada (producción)")
    print("4. Cargar Envíos desde CONSOLIDADO")
    print("5. Salir")
    print("=" * 60)

def main():
    while True:
        mostrar_menu()
        
        try:
            opcion = input("Seleccione una opción (1-5): ").strip()
            
            if opcion == "1":
                print("\n🔄 Iniciando sincronización detallada...")
                with ClienteSynchronizer() as sync:
                    sync.sincronizar_detallado()
                    
            elif opcion == "2":
                print("\n⚡ Iniciando sincronización simplificada...")
                with ClienteSynchronizer() as sync:
                    sync.sincronizar_simplificado()
                    
            elif opcion == "3":
                print("\n🚀 Iniciando sincronización optimizada...")
                with ClienteSynchronizer() as sync:
                    sync.sincronizar_optimizado()
                    
            elif opcion == "4":
                print("\n📁 Iniciando carga de envíos desde CONSOLIDADO...")
                with EnviosSynchronizer() as sync:
                    sync.sincronizar_envios()
                    
            elif opcion == "5":
                print("\n👋 ¡Hasta luego!")
                sys.exit(0)
                
            else:
                print("\n❌ Opción no válida. Por favor, seleccione 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Operación cancelada por el usuario.")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Por favor, verifique su configuración y vuelva a intentar.")
        
        input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    main() 