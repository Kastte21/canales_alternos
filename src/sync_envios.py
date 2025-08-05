#!/usr/bin/env python3
from src.sync.envios_synchronizer import EnviosSynchronizer

def main():
    try:
        with EnviosSynchronizer() as sync:
            sync.sincronizar_envios()
    except Exception as e:
        print(f"Error en sincronización de envíos: {e}")
        raise

if __name__ == "__main__":
    main() 