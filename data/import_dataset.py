import kagglehub

# Download latest version
path = kagglehub.dataset_download("shriyashjagtap/indian-personal-finance-and-spending-habits")

print("Path to dataset files:", path)