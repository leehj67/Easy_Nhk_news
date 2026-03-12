@echo off
REM NHK Easy Reader - 올바른 Python 환경으로 실행
python -m pip install -q psycopg2-binary 2>nul
python -m streamlit run app.py %*
