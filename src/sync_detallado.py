#!/usr/bin/env python3
from src.sync.synchronizer import ClienteSynchronizer

def main():
    try:
        with ClienteSynchronizer() as sync:
            sync.sincronizar_detallado()
    except Exception as e:
        print(f"Error en sincronización detallada: {e}")
        raise

if __name__ == "__main__":
    main() 