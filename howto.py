# 1) Find the actual cluster service
pg_lsclusters
# Example output: 18 main 5432 ...

# 2) Start/enable the real cluster service (replace 18 if yours differs)
sudo systemctl start postgresql@18-main
sudo systemctl enable postgresql@18-main
sudo systemctl status postgresql@18-main


sudo ss -ltnp | awk '$4 ~ /:5432$/'

source venv/bin/activate
uvicorn app.main:app --reload --port 8000
