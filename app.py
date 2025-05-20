import os
from flask import Flask, request, send_file, render_template, redirect, url_for
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import DictionaryObject, NameObject, ArrayObject, IndirectObject
from io import BytesIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """
    Renders the main upload page.
    """
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handles PDF file uploads, reads basic text, and prepares for form filling.
    """
    if 'pdf_file' not in request.files:
        return redirect(request.url)
    pdf_file = request.files['pdf_file']
    if pdf_file.filename == '':
        return redirect(request.url)

    if pdf_file and pdf_file.filename.endswith('.pdf'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
        pdf_file.save(filepath)

        reader = PdfReader(filepath)
        form_fields = {}
        if reader.forms:
            # Extract form fields for display
            for field_name in reader.forms.get_fields():
                form_fields[field_name] = "" # Initialize with empty string
        
        # We'll save the uploaded filename in the session or pass it
        # for further processing. For simplicity now, we'll just return it.
        return render_template('fill_form.html', filename=pdf_file.filename, form_fields=form_fields)
    
    return "Invalid file type. Please upload a PDF."

@app.route('/fill_and_sign/<filename>', methods=['POST'])
def fill_and_sign(filename):
    """
    Fills PDF form fields and adds a 'signature'.
    """
    input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], f'signed_{filename}')

    reader = PdfReader(input_filepath)
    writer = PdfWriter()

    # Add all pages to the writer
    for page in reader.pages:
        writer.add_page(page)

    # Fill form fields
    if reader.forms:
        for field_name in reader.forms.get_fields():
            field_value = request.form.get(field_name, '')
            if field_value:
                writer.update_page_form_field_values(writer.pages[0], {field_name: field_value})
                # Note: PyPDF2 might not flatten the fields automatically without a viewer.
                # To make fields non-editable, you'd typically flatten them.
                # For this simple example, we're just updating values.

    # Add a simple text "signature"
    signature_text = request.form.get('signature_text', 'Signed by User')
    # For a real signature, you might draw on a canvas or upload an image.
    # PyPDF2 doesn't have direct drawing capabilities. For that, you'd use reportlab or similar.
    # Here, we're just updating an existing field if it's named 'signature', or conceptually
    # acknowledging the "signature". If you want to *add* text to a specific coordinate,
    # you'd need a more advanced library or post-processing with ReportLab.
    # For now, let's assume we can update a field if it exists, otherwise, just process.
    if reader.forms and 'signature' in reader.forms.get_fields():
         writer.update_page_form_field_values(writer.pages[0], {'signature': signature_text})


    # Save the modified PDF
    with open(output_filepath, "wb") as output_pdf:
        writer.write(output_pdf)

    return send_file(output_filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
