Sana Commerce Image Preparation Tool
====================================

**Developed by One Thing Digital**

This desktop application automates the process of preparing product images for import into Sana Commerce. It takes a CSV mapping file and a folder of raw images, then automatically renames, resizes, and optimizes the images to match your SKUs, ready for upload to the Sana File Manager.

Features
--------

*   **Automated Renaming:** Matches images from a CSV (even if they have URLs or paths) and renames them to Sana standards (SKU\_1.jpg, SKU\_2.jpg).
    
*   **Smart Search:** Finds images in your source folder regardless of case sensitivity.
    
*   **Optimization:** Convert formats (JPG, PNG, WebP) and adjust quality compression.
    
*   **Resizing:** optional constraints for max width/height to ensure uniform web-ready images.
    
*   **Error Reporting:** Generates a text file report of any missing images or bad SKUs.
    

Developer Setup
---------------

If you want to run the raw Python script or modify the code, follow these steps:

1.  git clone \[https://github.com/YourUsername/sana-image-tool.git\](https://github.com/YourUsername/sana-image-tool.git)cd sana-image-tool
    
2.  \# Windowspython -m venv venvvenv\\Scripts\\activate# Mac/Linuxpython3 -m venv venvsource venv/bin/activate
    
3.  pip install -r requirements.txt
    
4.  python image\_sku\_processor.py
    

Building the Executable (.exe)
------------------------------

To package this tool into a single .exe file that can be shared with clients or staff (no Python installation required):

1.  Ensure you have your icon file (app\_icon.ico) in the root directory.
    
2.  pyinstaller --noconsole --onefile --icon=app\_icon.ico image\_sku\_processor.py
    
3.  The standalone application will be created in the dist/ folder.
    

User Guide
----------

1.  **Launch the Tool:** Double-click the application.
    
2.  **Select Files:**
    
    *   **CSV Spreadsheet:** Select your export file. The tool expects **Column A** to be the SKU, and subsequent columns (B, C, etc.) to contain image filenames or URLs.
        
    *   **Source Folder:** The folder containing your raw, disorganized images.
        
    *   **Output Folder:** An empty folder where the clean files will be saved.
        
3.  **Configure Settings:** Choose your desired output format (e.g., JPG or WebP) and quality settings.
    
4.  **Run:** Click "Start Processing Images".
    
5.  **Upload:** Once finished, upload the contents of the Output Folder to your Sana Commerce File Manager.
    

Support
-------

For questions, comments, or help with Sana Commerce integrations, please contact us:

*   **Website:** [onethingdigital.com](https://onethingdigital.com/)
    
*   **Contact:** [onethingdigital.com/contact-us](https://www.google.com/search?q=https://onethingdigital.com/contact-us)