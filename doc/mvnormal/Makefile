default-target: all
default-target: .PHONY
.PHONY:

PDFLATEX = pdflatex

all: .PHONY
all: pdf

pdf: .PHONY
pdf: mvnormal.pdf

clean: .PHONY
clean: clean-mvnormal

mvnormal.pdf: mvnormal.tex
	$(PDFLATEX) \\nonstopmode\\input mvnormal
	$(PDFLATEX) \\nonstopmode\\input mvnormal
	$(PDFLATEX) \\nonstopmode\\input mvnormal

clean-mvnormal: .PHONY
	-rm -f mvnormal.aux
	-rm -f mvnormal.log
	-rm -f mvnormal.pdf
