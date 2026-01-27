import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import sys  # Added sys to check for bundled exe path
import csv
from PIL import Image, ImageOps
import threading
import datetime
import webbrowser

# ------------------------------------------------------------------------------
# CONFIG & ASSETS
# ------------------------------------------------------------------------------

COLORS = {
    "primary": "#00529D",       # Polynesian Blue
    "accent": "#034078",        # Indigo Dye
    "bg_main": "#FCFDFD",       # White (Frost)
    "bg_sec": "#E7ECEF",        # Off White (Anti Flash White)
    "text_body": "#131112",     # Night
    "text_sub": "#434343",      # Onyx
    "border": "#969696",        # Battleship Gray
    "success": "#6BAF46",       # Kelly Green
    "error": "#9D2F2F",         # Auburn / Red
}

FONTS = {
    "header": ("Helvetica", 14, "bold"),
    "sub_header": ("Helvetica", 11, "bold"),
    "body": ("Helvetica", 10),
    "small": ("Helvetica", 9),
    "mono": ("Consolas", 9)
}

# ------------------------------------------------------------------------------
# LOGIC & PROCESSING
# ------------------------------------------------------------------------------

class ImageProcessorLogic:
    def __init__(self, log_callback, progress_callback):
        self.log = log_callback
        self.update_progress = progress_callback
        self.stop_event = threading.Event()

    def clean_filename(self, path_str):
        """
        Extracts just the filename from a URL or full path.
        Ex: 'http://site.com/img/photo.jpg' -> 'photo.jpg'
        Ex: 'C:\\Users\\Data\\photo.jpg' -> 'photo.jpg'
        """
        if not path_str:
            return ""
        # Normalize slashes to forward slashes, then split
        name = path_str.replace('\\', '/').split('/')[-1]
        return name.strip()

    def find_file(self, filename, search_path):
        """
        Attempts to find a file in the search_path.
        Case-insensitive matching is attempted if exact match fails.
        Strictly looks in search_path only (no recursive subfolders).
        """
        if not filename:
            return None
            
        # 1. Exact match
        full_path = os.path.join(search_path, filename)
        if os.path.isfile(full_path):
            return full_path

        # 2. Case-insensitive search (scans only the immediate directory)
        filename_lower = filename.lower()
        try:
            for f in os.listdir(search_path):
                # Check if it matches name AND is actually a file
                if f.lower() == filename_lower:
                    found_path = os.path.join(search_path, f)
                    if os.path.isfile(found_path):
                        return found_path
        except OSError as e:
            self.log(f"Error accessing directory: {e}")
            return None
        
        return None

    def process_images(self, settings):
        csv_path = settings['csv_path']
        src_dir = settings['src_dir']
        out_dir = settings['out_dir']
        output_format = settings['format'].lower()
        quality = settings['quality']
        max_width = settings['max_width']
        max_height = settings['max_height']
        allow_upscale = settings['allow_upscale']
        
        error_log = [] 

        # Read CSV
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
        except Exception as e:
            err_msg = f"CRITICAL ERROR: Could not read CSV file. {e}"
            self.log(err_msg)
            messagebox.showerror("CSV Error", err_msg)
            return

        if not rows:
            self.log("CSV is empty.")
            return
        
        # Skip header
        header = rows.pop(0) 
        total_rows = len(rows)
        self.log(f"Found {total_rows} lines to process.")

        processed_count = 0
        
        for i, row in enumerate(rows):
            if self.stop_event.is_set():
                self.log("Processing stopped by user.")
                break

            if not row or not any(row): 
                continue

            if len(row) < 2:
                msg = f"Line {i+2}: Skipped (Not enough columns - need SKU and 1 image)"
                self.log(msg)
                error_log.append(msg)
                processed_count += 1
                continue

            sku = row[0].strip()
            # Clean SKU to be filename safe
            sku_safe = "".join([c for c in sku if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
            
            if not sku_safe:
                msg = f"Line {i+2}: Skipped (Invalid or empty SKU)"
                self.log(msg)
                error_log.append(msg)
                processed_count += 1
                continue

            # Extract filenames from URL/Path strings in columns
            raw_images = [x.strip() for x in row[1:] if x.strip()]
            image_files = [self.clean_filename(x) for x in raw_images]
            
            if not image_files:
                msg = f"SKU {sku}: Skipped (No valid image filenames found)"
                self.log(msg)
                error_log.append(msg)
                processed_count += 1
                continue

            self.log(f"Processing SKU: {sku} ({len(image_files)} images)")

            for idx, img_filename in enumerate(image_files, 1):
                src_file_path = self.find_file(img_filename, src_dir)
                
                if not src_file_path:
                    msg = f"SKU {sku}: Image not found -> '{img_filename}'"
                    self.log(f"  [MISSING] {img_filename}")
                    error_log.append(msg)
                    continue

                try:
                    with Image.open(src_file_path) as img:
                        # Convert/Handle Transparency
                        if output_format in ['jpeg', 'jpg'] and img.mode in ('RGBA', 'LA'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[-1])
                            img = background
                        elif output_format != 'jpeg':
                            if img.mode == 'CMYK':
                                img = img.convert('RGB')

                        # Resizing Logic
                        if max_width > 0 or max_height > 0:
                            current_w, current_h = img.size
                            target_w = max_width if max_width > 0 else current_w
                            target_h = max_height if max_height > 0 else current_h
                            
                            if not allow_upscale:
                                target_w = min(target_w, current_w)
                                target_h = min(target_h, current_h)

                            img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

                        # Output Filename Construction
                        new_filename = f"{sku_safe}_{idx}.{output_format}"
                        out_path = os.path.join(out_dir, new_filename)

                        # Save
                        save_kwargs = {}
                        if output_format in ['jpeg', 'jpg']:
                            save_kwargs['quality'] = quality
                            save_kwargs['optimize'] = True
                        elif output_format == 'webp':
                            save_kwargs['quality'] = quality
                        elif output_format == 'png':
                            save_kwargs['optimize'] = True

                        img.save(out_path, **save_kwargs)
                        self.log(f"  -> Saved {new_filename}")

                except Exception as e:
                    msg = f"SKU {sku}: Error processing '{img_filename}' -> {str(e)}"
                    self.log(f"  [ERROR] {e}")
                    error_log.append(msg)

            processed_count += 1
            progress_pct = (processed_count / total_rows) * 100
            self.update_progress(progress_pct)

        # Generate Error Report
        if error_log:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            report_filename = f"_Error_Report_{timestamp}.txt"
            report_path = os.path.join(out_dir, report_filename)
            try:
                with open(report_path, "w", encoding='utf-8') as f:
                    f.write(f"Batch Processing Error Report\nGenerated: {timestamp}\n")
                    f.write("==================================================\n\n")
                    for err in error_log:
                        f.write(err + "\n")
                self.log(f"\nWARNING: {len(error_log)} errors occurred.")
                self.log(f"Report saved to: {report_filename}")
                messagebox.showwarning("Completed with Errors", f"Processing finished with {len(error_log)} errors.\nCheck the '_Error_Report' file in the output folder.")
            except Exception as e:
                self.log(f"Could not write error report: {e}")
        else:
            self.log("\nSuccess! No errors found.")
            messagebox.showinfo("Success", "Batch processing complete with no errors.")

        self.update_progress(100)

# ------------------------------------------------------------------------------
# GUI
# ------------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sana Commerce Image Preparation Tool")
        # Ensure window is large enough for footer
        self.geometry("800x850")
        self.minsize(800, 850)
        self.configure(bg=COLORS["bg_main"])
        
        # --- ICON SETUP (Fix for Feather Icon) ---
        # Determine the path to the icon whether running as script or frozen exe
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller exe - look in temp folder
            application_path = sys._MEIPASS
        else:
            # Running as script - look in current folder
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(application_path, 'app_icon.ico')
        
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass # Fail silently and use default if icon is corrupt
        # ------------------------------------------

        self.setup_styles()
        
        self.settings = {
            'csv_path': tk.StringVar(),
            'src_dir': tk.StringVar(),
            'out_dir': tk.StringVar(),
            'format': tk.StringVar(value='jpg'),
            'quality': tk.IntVar(value=85),
            'max_width': tk.IntVar(value=0),
            'max_height': tk.IntVar(value=0),
            'allow_upscale': tk.BooleanVar(value=False)
        }

        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        
        # General Defaults
        style.configure(".", background=COLORS["bg_main"], font=FONTS["body"], foreground=COLORS["text_body"])
        
        # Frames
        style.configure("TFrame", background=COLORS["bg_main"])
        style.configure("Card.TFrame", background=COLORS["bg_sec"], relief="flat")
        style.configure("Footer.TFrame", background=COLORS["bg_sec"])

        # Labelframes
        style.configure("TLabelframe", background=COLORS["bg_main"], bordercolor=COLORS["border"])
        style.configure("TLabelframe.Label", background=COLORS["bg_main"], foreground=COLORS["primary"], font=FONTS["sub_header"])

        # Buttons
        style.configure("TButton", 
            background=COLORS["primary"], 
            foreground="white", 
            font=FONTS["sub_header"],
            borderwidth=0,
            focuscolor=COLORS["accent"],
            padding=10
        )
        style.map("TButton", 
            background=[('active', COLORS["accent"]), ('disabled', COLORS["border"])],
            foreground=[('disabled', '#eeeeee')]
        )
        
        # Browse Button (smaller, distinct)
        style.configure("Browse.TButton", 
            background=COLORS["bg_sec"], 
            foreground=COLORS["primary"],
            font=FONTS["small"],
            padding=5,
            borderwidth=1,
            bordercolor=COLORS["primary"]
        )
        style.map("Browse.TButton", background=[('active', '#dbe0e3')])

        # Labels
        style.configure("Header.TLabel", font=FONTS["header"], foreground=COLORS["primary"])
        style.configure("Sub.TLabel", font=FONTS["small"], foreground=COLORS["text_sub"])
        
        # Progress Bar
        style.configure("Horizontal.TProgressbar", background=COLORS["success"], troughcolor=COLORS["bg_sec"], borderwidth=0)

    def create_widgets(self):
        # --- HEADER ---
        header_frame = ttk.Frame(self, padding="20 20 20 5")
        header_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(header_frame, text="Sana Commerce Image Tool", style="Header.TLabel").pack(anchor='w')
        ttk.Label(header_frame, text="Prepare and rename product images for Sana Commerce import.", style="Sub.TLabel").pack(anchor='w')

        # --- INSTRUCTIONS LINK ---
        instr_frame = ttk.Frame(self, padding="20 0 20 5")
        instr_frame.pack(side=tk.TOP, fill=tk.X)
        instr_lbl = ttk.Label(instr_frame, text="View Instructions (Click Here)", 
                            cursor="hand2", foreground=COLORS["primary"], font=FONTS["sub_header"])
        instr_lbl.pack(anchor='w')
        instr_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://onethingdigital.com/blog/sana-image-tool"))

        # --- FOOTER (Branding) ---
        # Packed BEFORE main content so it sticks to bottom reliably
        footer_frame = ttk.Frame(self, padding="15", style="Footer.TFrame")
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)

        dev_lbl = ttk.Label(footer_frame, text="Developed by One Thing Digital", 
                           background=COLORS["bg_sec"], font=FONTS["sub_header"], foreground=COLORS["text_body"])
        dev_lbl.pack(anchor='center')

        sub_lbl = ttk.Label(footer_frame, text="For Sana Commerce Image Import Integration", 
                           background=COLORS["bg_sec"], style="Sub.TLabel")
        sub_lbl.pack(anchor='center', pady=(2, 5))

        # Contact Link
        contact_lbl = ttk.Label(footer_frame, text="Need help? Contact us at onethingdigital.com/contact-us", 
                            background=COLORS["bg_sec"], foreground=COLORS["text_sub"], font=FONTS["small"], cursor="hand2")
        contact_lbl.pack(anchor='center')
        contact_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://onethingdigital.com/contact-us"))

        # --- MAIN CONTENT ---
        # Packed LAST so it consumes only the REMAINING space between header and footer
        main_frame = ttk.Frame(self, padding="20 0 20 20")
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 1. File Locations
        path_frame = ttk.LabelFrame(main_frame, text="1. File Locations", padding="15")
        path_frame.pack(fill=tk.X, pady=10)

        self.create_file_selector(path_frame, "CSV Spreadsheet:", self.settings['csv_path'], is_file=True)
        self.create_file_selector(path_frame, "Images Source Folder:", self.settings['src_dir'], is_file=False)
        self.create_file_selector(path_frame, "Output Folder:", self.settings['out_dir'], is_file=False)

        # 2. Settings
        settings_frame = ttk.LabelFrame(main_frame, text="2. Optimization Settings", padding="15")
        settings_frame.pack(fill=tk.X, pady=10)

        # Grid layout for settings
        # Format
        ttk.Label(settings_frame, text="Output Format:").grid(row=0, column=0, sticky='w', pady=10)
        format_cb = ttk.Combobox(settings_frame, textvariable=self.settings['format'], values=['jpg', 'png', 'webp'], state="readonly", width=12)
        format_cb.grid(row=0, column=1, sticky='w', padx=10)

        # Quality
        ttk.Label(settings_frame, text="Quality (1-100):").grid(row=0, column=2, sticky='w', pady=10, padx=20)
        qual_scale = tk.Scale(settings_frame, from_=1, to=100, orient=tk.HORIZONTAL, variable=self.settings['quality'], 
                              length=150, bg=COLORS["bg_main"], highlightthickness=0, fg=COLORS["text_body"])
        qual_scale.grid(row=0, column=3, sticky='w')

        # Dimensions
        ttk.Label(settings_frame, text="Resize Max Width:").grid(row=1, column=0, sticky='w', pady=10)
        ttk.Entry(settings_frame, textvariable=self.settings['max_width'], width=12).grid(row=1, column=1, sticky='w', padx=10)
        
        ttk.Label(settings_frame, text="Resize Max Height:").grid(row=1, column=2, sticky='w', pady=10, padx=20)
        ttk.Entry(settings_frame, textvariable=self.settings['max_height'], width=12).grid(row=1, column=3, sticky='w')

        ttk.Label(settings_frame, text="(0 = auto)", style="Sub.TLabel").grid(row=1, column=4, sticky='w')

        # Upscale toggle
        chk = ttk.Checkbutton(settings_frame, text="Allow Upscaling (Not recommended)", variable=self.settings['allow_upscale'])
        chk.grid(row=2, column=0, columnspan=3, sticky='w', pady=10)

        # 3. Actions & Log
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.btn_run = ttk.Button(action_frame, text="Start Processing Images", command=self.start_processing)
        self.btn_run.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        self.progress = ttk.Progressbar(action_frame, orient=tk.HORIZONTAL, length=100, mode='determinate', style="Horizontal.TProgressbar")
        self.progress.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        # Log Area
        log_frame = ttk.Frame(action_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(log_frame, text="Processing Log:", style="Sub.TLabel").pack(anchor='w')
        
        self.log_text = tk.Text(log_frame, height=8, state='disabled', font=FONTS["mono"], 
                                bg="#f4f4f4", relief="flat", padx=10, pady=10)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text['yscrollcommand'] = scrollbar.set

    def create_file_selector(self, parent, label, var, is_file):
        container = ttk.Frame(parent)
        container.pack(fill=tk.X, pady=5)
        
        ttk.Label(container, text=label, width=20).pack(side=tk.LEFT)
        
        entry = ttk.Entry(container, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        def browse():
            if is_file:
                path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
            else:
                path = filedialog.askdirectory()
            if path:
                var.set(path)
                
        ttk.Button(container, text="Browse...", style="Browse.TButton", command=browse).pack(side=tk.LEFT)

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def update_progress(self, percent):
        self.progress['value'] = percent
        self.update_idletasks()

    def start_processing(self):
        # Validate
        if not all([self.settings['csv_path'].get(), self.settings['src_dir'].get(), self.settings['out_dir'].get()]):
            messagebox.showerror("Missing Information", "Please select the CSV file, Source folder, and Output folder.")
            return

        # Disable button
        self.btn_run.config(state='disabled')
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

        # Prepare settings dict
        current_settings = {
            'csv_path': self.settings['csv_path'].get(),
            'src_dir': self.settings['src_dir'].get(),
            'out_dir': self.settings['out_dir'].get(),
            'format': self.settings['format'].get(),
            'quality': self.settings['quality'].get(),
            'max_width': self.settings['max_width'].get(),
            'max_height': self.settings['max_height'].get(),
            'allow_upscale': self.settings['allow_upscale'].get(),
        }

        # Run in thread to keep GUI responsive
        def run_thread():
            processor = ImageProcessorLogic(self.log, self.update_progress)
            processor.process_images(current_settings)
            self.btn_run.config(state='normal')

        threading.Thread(target=run_thread, daemon=True).start()

if __name__ == "__main__":
    app = App()
    app.mainloop()