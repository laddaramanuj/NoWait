import os
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Supabase setup
SUPABASE_URL = "https://wtzyfsbvymtpcrspkjau.supabase.co"  # Fetch URL from environment variables
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0enlmc2J2eW10cGNyc3BramF1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ1MDAwOTAsImV4cCI6MjA1MDA3NjA5MH0.sVDo1dv7ZLi7wYwGAl_frC1QAKn1jPZIGfk2xTXL_FQ"  # Fetch anon key from environment variables
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# File upload configurations
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# Function to check if the file extension is allowed
def allowed_file(filename: str):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Helper function to upload the image to Supabase Storage
def upload_image_to_supabase(filename: str) -> str:
    bucket_name = 'menu-images'
    file_path = f'public/{filename}'

    with open(os.path.join(UPLOAD_FOLDER, filename), "rb") as file:
        response = supabase_client.storage.from_(bucket_name).upload(file_path, file)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error uploading image to Supabase.")

    os.remove(os.path.join(UPLOAD_FOLDER, filename))

    return f'https://nowait.supabase.co/storage/v1/object/public/{file_path}'


# Endpoint to get the HTML page
@app.get("/", response_class=HTMLResponse)
async def get_html_page():
    with open("static/upload_restaurant.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


@app.get("/{restaurant_id}/menu", response_class=HTMLResponse)
async def get_html_page():
    with open("static/upload_menu_item.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


# Endpoint to upload restaurant data
# Endpoint to upload restaurant data
@app.post("/")
async def upload_restaurant(
        name: str = Form(...),
        address: str = Form(...),
        contact: str = Form(...),
        email: str = Form(...),
        opening_hours: str = Form(...),  # Add this field to handle opening_hours
        is_open: bool = Form(...),       # Add this field to handle is_open
):

    restaurant_data = {
        'name': name,
        'address': address,
        'contact': contact,
        'email': email,
        'opening_hours': opening_hours,  # Add this to the database insert data
        'is_open': is_open,              # Add this to the database insert data
    }

    response = supabase_client.table('restaurants').insert(restaurant_data).execute()

    # Check if the insertion was successful
    if response.data is None or len(response.data) == 0:
        raise HTTPException(status_code=500, detail=f"Error inserting restaurant: {response.error_message if response.error_message else 'Unknown error'}")

    return JSONResponse(content=response.data[0], status_code=201)



# Endpoint to upload menu item data
@app.post("/{restaurant_id}/menu")
async def upload_menu_item(
        restaurant_id: int,
        name: str = Form(...),
        description: str = Form(...),
        price: float = Form(...),
        make_time: int = Form(...),
        calories: int = Form(...),
        ingredients: str = Form(...),
        is_vegetarian: bool = Form(...),
        is_vegan: bool = Form(...),
        is_gluten_free: bool = Form(...),
        spice_level: str = Form(...),
        serving_size: str = Form(...),
        category_id: int = Form(...),
        image: UploadFile = File(...),
):
    if not allowed_file(image.filename):
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")

    file_path = os.path.join(UPLOAD_FOLDER, image.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await image.read())

    image_url = upload_image_to_supabase(image.filename)

    menu_item_data = {
        'restaurant_id': restaurant_id,
        'name': name,
        'description': description,
        'price': price,
        'make_time': make_time,
        'calories': calories,
        'ingredients': ingredients,
        'is_vegetarian': is_vegetarian,
        'is_vegan': is_vegan,
        'is_gluten_free': is_gluten_free,
        'spice_level': spice_level,
        'serving_size': serving_size,
        'image_url': image_url,
        'category_id': category_id,
    }

    response = supabase_client.table('menu_items').insert(menu_item_data).execute()

    if response.status_code != 201:
        raise HTTPException(status_code=500, detail=f"Error inserting menu item: {response.error_message}")

    return JSONResponse(content=response.data[0], status_code=201)


# Run the FastAPI app directly if this file is executed as a script
if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
