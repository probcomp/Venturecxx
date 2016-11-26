default-target: all
default-target: .PHONY
.PHONY:

PDFLATEX = pdflatex

all: .PHONY
all: intuiting-kl.pdf

clean: .PHONY
clean: clean-intuiting-kl

clean-intuiting-kl: .PHONY
	-rm -f intuiting-kl.aux
	-rm -f intuiting-kl.log
	-rm -f intuiting-kl.pdf

.SUFFIXES: .pdf
.SUFFIXES: .tex

.tex.pdf:
	$(PDFLATEX) \\nonstopmode\\input $<
	$(PDFLATEX) \\nonstopmode\\input $<
	$(PDFLATEX) \\nonstopmode\\input $<
