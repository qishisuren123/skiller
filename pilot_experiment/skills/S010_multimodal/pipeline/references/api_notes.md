# PIL (Pillow) - Image processing
Image.open(path)          # Open image file
img.verify()              # Check if image is corrupted (closes image)
img.resize((w, h))        # Resize image to specified dimensions
img.save(path)            # Save image to file
img.size                  # Get image dimensions as (width, height)

# pandas - CSV handling
pd.read_csv(path)         # Read CSV file into DataFrame
df.columns                # Get column names
dict(zip(df['col1'], df['col2']))  # Create dictionary from two columns

# shutil - File operations
shutil.copy2(src, dst)    # Copy file preserving metadata

# os - Directory operations
os.makedirs(path, exist_ok=True)  # Create directory (no error if exists)
os.path.join(a, b)        # Join path components
os.path.exists(path)      # Check if path exists
os.listdir(dir)           # List directory contents
