#!/bin/sh

# Reset the working directory to the script's path

# Actually run the tests
python -c "import render_example as r; r.renderAllSchematics()"
cd pdf_graphs
pdflatex schematics.tex
pdflatex schematics.tex
pdflatex schematics.tex
cd ..
cp pdf_graphs/schematics.pdf schematics.pdf
echo "See schematics.pdf"
