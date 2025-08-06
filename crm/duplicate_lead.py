import frappe
from frappe.utils import now


def normalize_egyptian_phone(number):
    if not number:
        return ""

    arabic_to_english = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    number = number.strip().replace(" ", "").replace("-", "")
    number = number.translate(arabic_to_english)

    # Now handle all common Egyptian number formats
    if number.startswith("+20"):
        return number
    elif number.startswith("0020"):
        return "+20" + number[4:]
    elif number.startswith("20"):
        return "+20" + number[2:]
    elif number.startswith("0"):
        return "+20" + number[1:]
    elif len(number) == 10 and number.startswith("1"):
        return "+20" + number
    elif len(number) == 11 and number.startswith("01"):
        return "+20" + number[1:]
    else:
        return number
    

# 🔹 Step 1: Check and mark duplicate
def check_duplicates(doc, method):
    frappe.log_error(f"check_duplicates called for: {doc.name}", "DEBUG")
    doc.phone = normalize_egyptian_phone(doc.phone)
    doc.mobile_no = normalize_egyptian_phone(doc.mobile_no)
    
    frappe.log_error(f"Normalized phone: {doc.phone} | mobile: {doc.mobile_no}", "DEBUG")


    if getattr(doc.flags, "ignore_duplicate_check", False):
        return

    if not doc.phone and not doc.mobile_no:
        return
    
    # Fetch oldest duplicate by phone or mobile_no
    duplicate_leads = frappe.get_all(
        "CRM Lead",
        filters={
            "name": ["!=", doc.name],
            "phone": doc.phone or "",
            "mobile_no": doc.mobile_no or ""
        },
        order_by="creation asc",
        fields=["name", "lead_owner"]
    )

    if duplicate_leads:
        original_lead_name = duplicate_leads[0]["name"]

        # Mark the current lead
        doc.is_duplicate = 1
        doc.duplicated_from = original_lead_name

        frappe.msgprint(
            msg=f"Phone number already exists for Lead {original_lead_name}. Your entry has been marked as duplicate.",
            indicator="orange",
            alert=True
        )

        doc.flags.ignore_duplicate_check = True


# 🔹 Step 2: Append to original lead’s duplicate_leads child table
def append_to_original_lead(doc, method):
    timestamp=now()
    if not doc.is_duplicate or not doc.duplicated_from:
        return

    try:
        original = frappe.get_doc("CRM Lead", doc.duplicated_from)
        
        row = {
            "lead": doc.name,
            "created_on": timestamp,
            "note": "Write Note"
            
        }
        
        original.append("duplicate_leads", row)
        original.original_lead = 1
        original.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.log_error(
            title="Duplicate Append Success",
            message=f"Appended duplicate {doc.name} to {original.name}"
        )

    except Exception:
        frappe.log_error(
            title="Lead Duplicate Append Error",
            message=frappe.get_traceback()
        )