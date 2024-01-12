bind = "0.0.0.0:8080"  
workers = 4  # count of process
threads = 2  # count of thread.
max_requests = 1000  # maximun requests
timeout = 30  # maximum running time

# app module setting
app_module = 'panda_backend.wsgi:application'
