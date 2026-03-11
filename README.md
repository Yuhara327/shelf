# Introduction
Shelf is a personal library management software designed for macOS.  
It enables users to construct and visualize a comprehensive book database efficiently, featuring automated entry generation from barcode images.

[Download](https://www.dropbox.com/scl/fi/z5eodsae1h0umbh2l4ccd/Shelf.zip?rlkey=5i4i00m9c2nm7z19fj12cci73&st=5eahg6qd&dl=1)

# Usage Guide
## Getting Started

Upon launching the application, please execute the Refresh command (**Command + R**).  
On the initial run, a database file named `library.db` will be generated in the directory `/Users/{username}/Documents/Shelf`.  
All bibliographic data is persisted within this file. Please exercise caution, as any corruption of this file will render the data inaccessible via the software.

## Adding Books

### Via ISBN Input
To add a book using its ISBN, enter the code into the "ISBN of the book to add" field and press the **OK** button (**Command + S**). Please ensure that hyphens are omitted during entry.

### Via Barcode Images
To perform a batch import using barcode images, store the relevant image files in a single folder.  
Supported file formats: **.jpg, .jpeg, .png, .heic** In Shelf, select "Add from barcode image files" and choose the designated folder to initiate the bulk import process.

## Deleting Books

### Via ISBN Specification
To delete a specific entry, enter the ISBN into the "ISBN of the book to delete" field and press the **OK** button (**Command + S**).

### Bulk Deletion
You may perform bulk deletions by checking the "Delete" boxes within the data table and subsequently pressing the **OK** button.

## Classification Numbers
The "Classification Number" column is user-editable, allowing for the implementation of custom systems such as the Dewey Decimal Classification.  
**Note:** You must press the **OK** button (**Command + S**) after editing to commit the changes to the database.

## Read Status Checkbox
Users can manage their reading progress via the "Read" checkboxes.  
**Note:** You must press the **OK** button (**Command + S**) after modification to ensure the updated status is persisted.
