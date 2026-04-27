import requests
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

def fetch_and_display_image(username, period):
    """
    Fetches an image from the Flask app and displays it
    """
    # URL of your Flask app (adjust the port if needed)
    url = f"http://localhost:5000/{username}/{period}"
    
    try:
        # Fetch the image from the URL
        response = requests.get(url)
        
        if response.status_code == 200:
            # Create image from bytes
            image_data = io.BytesIO(response.content)
            image = Image.open(image_data)
            
            # Display the image
            image.show()
            logger.info("Displaying image for %s/%s", username, period)
            logger.info("Image size: %s", image.size)
            return image
        else:
            logger.error("Error fetching image: status_code=%s", response.status_code)
            return None
            
    except requests.RequestException:
        logger.exception("Network error while fetching image for %s/%s", username, period)
        return None

# Example usage
if __name__ == "__main__":
    # Fetch and display images for different users and periods
    logger.info("Fetching last month image for user1...")
    fetch_and_display_image("user1", "last_month")