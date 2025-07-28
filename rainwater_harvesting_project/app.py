from flask import Flask, render_template, request, make_response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch

app = Flask(__name__)

RUNOFF_MAP = {
    "Concrete": 0.85,
    "Tiled": 0.75,
    "Brick": 0.65
}

@app.route("/", methods=["GET", "POST"])
def index():
    data = None
    if request.method == "POST":
        roof_area = float(request.form["roof_area"])
        rainfall = float(request.form["rainfall"])
        roof_type = request.form["roof_type"]
        daily_need = float(request.form["daily_need"])
        days = int(request.form["days"])
        area = request.form["area"]

        runoff_coeff = RUNOFF_MAP.get(roof_type, 0.75)
        harvested_volume = roof_area * rainfall * runoff_coeff  # in liters
        required_volume = daily_need * days
        suggested_tank = max(required_volume, harvested_volume * 0.25)

        overflow_desc = (
            "Overflow system allows excess rainwater to exit safely, preventing tank damage or flooding. "
            "Typically includes an outlet pipe positioned below tank rim."
        )
        filtration_desc = (
            "Filtration system removes debris and contaminants from rainwater before storage, "
            "commonly including first-flush diverters, mesh screens, and sediment filters."
        )

        data = {
            "roof_area": roof_area,
            "rainfall": rainfall,
            "runoff_coeff": runoff_coeff,
            "roof_type": roof_type,
            "daily_need": daily_need,
            "days": days,
            "area": area,
            "harvested_volume": harvested_volume,
            "required_volume": required_volume,
            "suggested_tank": suggested_tank,
            "overflow_desc": overflow_desc,
            "filtration_desc": filtration_desc
        }

        if request.form.get("action") == "download":
            # Create PDF in memory
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Title
            p.setFont("Helvetica-Bold", 20)
            p.setFillColor(colors.darkblue)
            p.drawCentredString(width/2, height - inch, "Rainwater Harvesting System Report")

            # Draw a line
            p.setStrokeColor(colors.darkblue)
            p.setLineWidth(2)
            p.line(inch, height - inch - 10, width - inch, height - inch - 10)

            # Content start
            p.setFont("Helvetica", 12)
            y = height - inch - 40
            line_height = 18

            def draw_text(label, text):
                nonlocal y
                p.setFillColor(colors.darkred)
                p.drawString(inch, y, label)
                p.setFillColor(colors.black)
                p.drawString(inch + 150, y, text)
                y -= line_height

            draw_text("Area:", area)
            draw_text("Roof Type:", roof_type)
            draw_text("Roof Area (m²):", f"{roof_area:.2f}")
            draw_text("Annual Rainfall (mm):", f"{rainfall:.2f}")
            draw_text("Runoff Coefficient:", f"{runoff_coeff:.2f}")

            y -= 10
            p.setFillColor(colors.darkgreen)
            p.setFont("Helvetica-Bold", 14)
            p.drawString(inch, y, "Harvesting Data")
            y -= line_height

            p.setFont("Helvetica", 12)
            draw_text("Total Rainwater Harvested per Year (liters):", f"{harvested_volume:.2f}")
            draw_text(f"Household Water Requirement for {days} days (liters):", f"{required_volume:.2f}")
            draw_text("Suggested Storage Tank Size (liters):", f"{suggested_tank:.2f}")

            y -= 20
            p.setFillColor(colors.darkgreen)
            p.setFont("Helvetica-Bold", 14)
            p.drawString(inch, y, "Overflow System")
            y -= line_height
            p.setFillColor(colors.black)
            text = p.beginText(inch, y)
            text.setFont("Helvetica", 12)
            for line in overflow_desc.split(". "):
                text.textLine(line.strip())
                y -= line_height
            p.drawText(text)

            y -= 20
            p.setFillColor(colors.darkgreen)
            p.setFont("Helvetica-Bold", 14)
            p.drawString(inch, y, "Filtration System")
            y -= line_height
            p.setFillColor(colors.black)
            text = p.beginText(inch, y)
            text.setFont("Helvetica", 12)
            for line in filtration_desc.split(". "):
                text.textLine(line.strip())
                y -= line_height
            p.drawText(text)

            # Finalize PDF
            p.showPage()
            p.save()
            buffer.seek(0)

            response = make_response(buffer.read())
            response.headers["Content-Disposition"] = "attachment; filename=rainwater_report.pdf"
            response.mimetype = "application/pdf"
            return response

    return render_template("index.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
