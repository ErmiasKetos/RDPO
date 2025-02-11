def update_google_sheet(form_data):
    """Append a new purchase request to the Google Sheet."""
    client = get_google_sheets_client()
    if not client:
        return False

    try:
        # Replace this with your actual Google Sheet ID
        sheet = client.open_by_key("1Su8RA77O7kixU03jrm6DhDOAUYijW-JBBDZ7DK6ulrY").worksheet("purchase_summary")

        sheet.append_row([
            form_data['PO Number'],
            form_data['Requester'],
            form_data['Requester Email'],
            form_data['Request Date and Time'],
            form_data['Link'],
            form_data['Quantity'],
            form_data['Shipment Address'],
            form_data['Attention To'],
            form_data['Department'],
            form_data['Description'],
            form_data['Classification'],
            form_data['Urgency']
        ])
        return True
    except Exception as e:
        st.error(f"Error updating Google Sheet: {str(e)}")
        return False
