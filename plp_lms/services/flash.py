def flash(request, message, category="success"):
    request.session["_flash"] = {"message": message, "category": category}
