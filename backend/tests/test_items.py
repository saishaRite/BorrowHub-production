def test_list_categories_and_locations(client):
    res_cat = client.get("/api/items/categories")
    assert res_cat.status_code == 200
    assert len(res_cat.json()) == 8

    res_loc = client.get("/api/items/locations")
    assert res_loc.status_code == 200
    assert len(res_loc.json()) >= 7


def test_create_and_manage_item(client, auth_headers_student_a, auth_headers_student_b):
    # Student A creates listing
    payload = {
        "title": "Digital Storage Oscilloscope 100MHz",
        "category_id": 3,  # Lab Equipment
        "location_id": 1,  # Bhabha Bhavan
        "description": "2-channel DSO for digital electronics lab coursework.",
        "item_condition": "GOOD",
        "deposit_amount": 1000.00,
        "daily_fee": 75.00,
        "max_borrow_days": 5,
        "image_urls": ["https://images.unsplash.com/photo-1581092335397-9583fe92d232"]
    }
    res = client.post("/api/items", json=payload, headers=auth_headers_student_a)
    assert res.status_code == 201
    item_data = res.json()
    item_id = item_data["item_id"]
    assert item_data["title"] == payload["title"]
    assert item_data["daily_fee"] == "75.00"

    # Student A edits their own listing
    update_payload = {
        "daily_fee": 80.00,
        "description": "Updated description with probe cables included."
    }
    res_edit = client.put(f"/api/items/{item_id}", json=update_payload, headers=auth_headers_student_a)
    assert res_edit.status_code == 200
    assert res_edit.json()["daily_fee"] == "80.00"

    # Student B attempts to edit Student A's listing (Forbidden!)
    res_hack = client.put(f"/api/items/{item_id}", json={"daily_fee": 5.00}, headers=auth_headers_student_b)
    assert res_hack.status_code == 403
    assert "permission" in res_hack.json()["detail"].lower()

    # Student A archives their listing
    res_archive = client.delete(f"/api/items/{item_id}", headers=auth_headers_student_a)
    assert res_archive.status_code == 200

    # Ensure archived item is not displayed in public marketplace search
    res_search = client.get(f"/api/items?q=Oscilloscope")
    items = res_search.json()["items"]
    assert not any(it["item_id"] == item_id for it in items)
