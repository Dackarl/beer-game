@echo off
echo Iniciando Beer Game...
echo Cuando veas la linea "Local URL: http://localhost:8501", abre esa direccion
echo en 4 pestanas o ventanas distintas del navegador (una por jugador).
echo.
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd '/home/dackarl/BEAR GAME' && streamlit run app.py --server.port 8501"
echo.
echo El servidor se detuvo. Presiona una tecla para cerrar esta ventana.
pause >nul
