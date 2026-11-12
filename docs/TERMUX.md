# Instalación en Android / Termux

```bash
pkg update -y
pkg install python git -y
git clone https://github.com/TU_USUARIO/trading-ai-analyzer-pro.git
cd trading-ai-analyzer-pro
bash install.sh
python run.py
```

El instalador solicita de forma oculta el token de Telegram, el ID numérico del chat privado y la API key de Groq. El ID solicitado no es el número telefónico ni el nombre de usuario.

Editar credenciales:

```bash
python setup_config.py --edit
```

Actualizar el código:

```bash
git pull
python -m pip install -r requirements.txt
```

Ejecutar pruebas:

```bash
python -m unittest discover -s tests -v
```

Si Android suspende procesos en segundo plano, revisa las restricciones de batería de Termux. La disponibilidad depende del dispositivo y del sistema operativo.
