"""Script to generate realistic sample PDF files for the demo."""

from pathlib import Path

import pymupdf as fitz

sample_dir = Path(__file__).resolve().parent

# 1. Vendor Quotation Acme PDF
doc_quote = fitz.open()

# Page 1
p1 = doc_quote.new_page()
p1.insert_text(
    (50, 72),
    "ACME CLOUD SOLUTIONS LTD.\n"
    "Commercial Vendor Quotation\n"
    "Quotation Number: Q-2026-8841\n"
    "Date: November 02, 2026\n"
    "Validity: 60 Calendar Days\n"
    "Vendor Contact: sales@acmecloudsolutions.com\n\n"
    "Client: Global Enterprise Corp.\n"
    "Project: AI Document Processing Platform Infrastructure",
    fontsize=12,
)

# Page 2
p2 = doc_quote.new_page()
p2.insert_text(
    (50, 72),
    "COMMERCIAL TERMS & PRICING BREAKDOWN\n\n"
    "Vendor Name: Acme Solutions Ltd.\n"
    "Item 1: Enterprise Vector Search & Orchestration Nodes: $85,000 USD\n"
    "Item 2: Implementation & Compliance Support: $40,000 USD\n"
    "Total Quote Amount: $125,000 USD\n"
    "Currency: USD\n\n"
    "PAYMENT & DELIVERY TERMS:\n"
    "Payment Terms: Payment within 15 days upon receipt of invoice.\n"
    "Early Payment Discount: 2% discount if payment is made within 10 days.\n"
    "Delivery Terms: FOB Destination within 14 business days of order confirmation.\n"
    "Warranty Period: 24 Months full maintenance and patch support.",
    fontsize=12,
)

doc_quote.save(str(sample_dir / "Vendor_Quotation_Acme.pdf"))
doc_quote.close()

# 2. Corporate Procurement Policy PDF
doc_policy = fitz.open()

# Page 1
pol1 = doc_policy.new_page()
pol1.insert_text(
    (50, 72),
    "GLOBAL ENTERPRISE CORP.\n"
    "CORPORATE PROCUREMENT POLICY (STANDARD V4.2)\n"
    "Effective Date: January 01, 2026\n"
    "Scope: Global Procurement & Vendor Management\n\n"
    "Section 1: General Principles\n"
    "All vendor engagements must adhere to strict fiscal controls, auditability, and fair competition.",
    fontsize=12,
)

# Page 2
pol2 = doc_policy.new_page()
pol2.insert_text(
    (50, 72),
    "Section 2: Payment Terms & Discounts\n\n"
    "Standard Payment Terms: Standard payment terms shall be within 30 days from invoice date.\n"
    "Any contract or quotation specifying payment terms shorter than 30 days requires an explicit written exception.\n\n"
    "Section 3: Approval Thresholds\n"
    "- Contracts under $50,000 USD: Department Head Approval\n"
    "- Contracts between $50,000 and $100,000 USD: VP of Finance Approval\n"
    "- Contracts exceeding $100,000 USD: Mandatory CFO signoff and competitive RFP review.",
    fontsize=12,
)

# Page 3
pol3 = doc_policy.new_page()
pol3.insert_text(
    (50, 72),
    "Section 4: Compliance & Risk Management\n\n"
    "Advance Payments: Limited to a maximum of $50,000 USD or 25% of total contract value.\n"
    "Insurance Requirements: On-site contractors must maintain minimum $2,000,000 general liability insurance.\n"
    "Penalties & Disputes: Late delivery penalty is 0.5% per calendar week. Disputes settled via AAA arbitration.\n"
    "Sole-source procurement exemptions require written justification signed by the Chief Procurement Officer.",
    fontsize=12,
)

doc_policy.save(str(sample_dir / "Corporate_Procurement_Policy.pdf"))
doc_policy.close()

print("Generated sample PDF documents successfully.")
