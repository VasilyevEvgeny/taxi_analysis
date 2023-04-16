from PyPDF2 import PdfReader

# creating a pdf reader object
reader = PdfReader('2023-04-16.pdf')

# printing number of pages in pdf file
print(len(reader.pages))

# getting a specific page from the pdf file
page = reader.pages[0]

# extracting text from page
for page in reader.pages:
    text = page.extract_text()
    print(text)

    print(type(text))
