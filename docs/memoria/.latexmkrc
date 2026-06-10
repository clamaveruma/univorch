# latexmk configuration for the memoria build.
#
# Why this file exists: latexmk runs biber and the standard index
# (.idx) automatically, but it does NOT know about the nomencl package's
# glossary, which works through a separate .nlo -> .nls makeindex pass.
# Without this custom dependency the \printnomenclature output is empty
# and the glossary page silently disappears from the PDF.
#
# This teaches latexmk that whenever main.nlo changes it must run
# makeindex with the nomencl style to (re)generate main.nls, and to
# clean it up on `latexmk -c`.

add_cus_dep('nlo', 'nls', 0, 'makenomenclature');

sub makenomenclature {
    system("makeindex -s nomencl.ist -o \"$_[0].nls\" \"$_[0].nlo\"");
}

push @generated_exts, 'nlo', 'nls';
