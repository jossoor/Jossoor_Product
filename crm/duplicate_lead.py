import frappe
from frappe.utils import now

# 🔹 Step 1: Check and mark duplicate
def check_duplicates(doc, method):
    frappe.log_error(f"check_duplicates called for: {doc.name}", "DEBUG")

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
            "craeted_on": timestamp
          
            #"notes": "Auto-appended duplicate"
        }

        original.append("duplicate_leads", row)
        original.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.log_error(f"Successfully appended: {row}", "Duplicate Append Log")

    except Exception as e:
        frappe.log_error(f"Failed to append duplicate: {str(e)}", "Lead Duplicate Append Error")