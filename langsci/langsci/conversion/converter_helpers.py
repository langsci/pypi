
# pylint: disable=anomalous-backslash-in-string,consider-using-f-string

yanks = (
            "\\begin{flushleft}",
            "\\end{flushleft}",
            "\\centering",
            "\\rmfamily",
            "\\raggedright",
            "\\par ",
            "\\tablehead{}",
            "\\textstylepagenumber",
            "\\textstyleCharChar",
            "\\textstyleInternetlink",
            "\\textstylefootnotereference",
            "\\textstyleFootnoteTextChar",
            "\\textstylepagenumber",
            "\\textstyleappleconvertedspace",
            "\\textstyleDefaultParagraphFont",
            "\\pagestyle{Standard}",
            "\\hline",
            "\\begin{center}",
            "\\end{center}",
            "\\begin{styleNormal}",
            "\\end{styleNormal}",
            "\\begin{styleStandard}",
            "\\end{styleStandard}",
            "\\begin{styleBodytextC}",
            "\\end{styleBodytextC}",
            "\\begin{styleBodyTextFirst}",
            "\\end{styleBodyTextFirst}",
            "\\begin{styleIllustration}",
            "\\end{styleIllustration}",
            "\\begin{styleTabelle}",
            "\\end{styleTabelle}",
            "\\begin{styleCaption}",
            "\\end{styleCaption}",
            "\\begin{styleAbbildung}",
            "\\end{styleAbbildung}",
            "\\begin{styleTextbody}",
            "\\end{styleTextbody}",
            "\\begin{styleLangSciBulletList}",
            "\\end{styleLangSciBulletList}",
            "\\begin{stylelsBulletList}",
            "\\end{stylelsBulletList}",
            "\\maketitle",
            "\\arraybslash",
            "\\textstyleAbsatzStandardschriftart{}",
            "\\textstyleAbsatzStandardschriftart",
            "[Warning: Image ignored] % Unhandled or unsupported graphics:",
            "%\\setcounter{listWWNumileveli}{0}\n",
            "%\\setcounter{listWWNumilevelii}{0}\n",
            "%\\setcounter{listWWNumiileveli}{0}\n",
            "%\\setcounter{listWWNumiilevelii}{0}\n",
            "%\\setcounter{listLangSciLanginfoiileveli}{0}\n",
            "%\\setcounter{listlsLanginfoiileveli}{0}\n",
            "\\setcounter{itemize}{0}",
            "\\setcounter{page}{1}",
            "\\mdseries ",
        )

explicitreplacements = (
            (r"\'{a}", "á"),
            (r"\'{e}", "é"),
            (r"\'{i}", "í"),
            (r"\'{o}", "ó"),
            (r"\'{u}", "ú"),
            (r"\'{y}", "ý"),
            (r"\'{m}", "ḿ"),
            (r"\'{n}", "ń"),
            (r"\'{r}", "ŕ"),
            (r"\'{l}", "ĺ"),
            (r"\'{c}", "ć"),
            (r"\'{s}", "ś"),
            (r"\'{z}", "ź"),
            (r"\`{a}", "à"),
            (r"\`{e}", "è"),
            (r"\`{i}", "ì"),
            (r"\`{o}", "ò"),
            (r"\`{u}", "ù"),
            (r"\`{y}", "ỳ"),
            (r"\`{n}", "ǹ"),
            (r"\^{a}", "â"),
            (r"\^{e}", "ê"),
            (r"\^{i}", "î"),
            (r"\^{o}", "ô"),
            (r"\^{u}", "û"),
            (r"\^{y}", "ŷ"),
            (r"\^{c}", "ĉ"),
            (r"\^{s}", "ŝ"),
            (r"\^{z}", "ẑ"),
            (r"\~{a}", "ã"),
            (r"\~{e}", "ẽ"),
            (r"\~{i}", "ĩ"),
            (r"\~{o}", "õ"),
            (r"\~{u}", "ũ"),
            (r"\~{y}", "ỹ"),
            (r"\~{n}", "ñ"),
            (r"\"{a}", "ä"),
            (r"\"{e}", "ë"),
            (r"\"{i}", "ï"),
            (r"\"{o}", "ö"),
            (r"\"{u}", "ü"),
            (r"\"{y}", "ÿ"),
            (r"\"{A}", "Ä"),
            (r"\"{E}", "Ë"),
            (r"\"{I}", "Ï"),
            (r"\"{O}", "Ö"),
            (r"\"{U}", "Ü"),
            (r"\"{Y}", "Ÿ"),
            (r"\v{a}", "ǎ"),
            (r"\v{e}", "ě"),
            (r"\v{i}", "ǐ"),
            (r"\v{o}", "ǒ"),
            (r"\v{u}", "ǔ"),
            (r"\v{n}", "ň"),
            (r"\v{r}", "ř"),
            (r"\v{c}", "č"),
            (r"\v{s}", "š"),
            (r"\v{z}", "ž"),
            (r"\v{C}", "Č"),
            (r"\v{S}", "Š"),
            (r"\v{Y}", "Ž"),
            (r"\u{a}", "ă"),
            (r"\u{e}", "ĕ"),
            (r"\u{i}", "ĭ"),
            (r"\u{\i}", "ĭ"),
            (r"\u{o}", "ŏ"),
            (r"\u{u}", "ŭ"),
            (r"\u{A}", "Ă"),
            (r"\u{E}", "Ĕ"),
            (r"\u{I}", "Ĭ"),
            (r"\u{O}", "Ŏ"),
            (r"\u{U}", "Ŭ"),
            (r"\={a}", "ā"),
            (r"\={e}", "ē"),
            (r"\={i}", "ī"),
            (r"\={\i}", "ī"),
            (r"\=\i", "ī"),
            (r"\={o}", "ō"),
            (r"\={u}", "ū"),
            (r"\={A}", "Ā"),
            (r"\={E}", "Ē"),
            (r"\={I}", "Ī"),
            (r"\={O}", "Ō"),
            (r"\={U}", "Ū"),
            (r"\=a", "ā"),
            (r"\=e", "ē"),
            (r"\=i", "ī"),
            (r"\=o", "ō"),
            (r"\=u", "ū"),
            (r"\=A", "Ā"),
            (r"\=E", "Ē"),
            (r"\=I", "Ī"),
            (r"\=O", "Ō"),
            (r"\=U", "Ū"),
            (r"$\alpha $", "α"),
            (r"$\beta $", "β"),
            (r"$\gamma $", "γ"),
            (r"$\delta $", "δ"),
            (r"$\epsilon $", "ε"),
            (r"$\zeta $", "ζ"),
            (r"$\eta $", "η"),
            (r"$\theta $", "θ"),
            (r"$\iota $", "ι"),
            (r"$\kappa $", "κ"),
            (r"$\lambda $", "λ"),
            (r"$\mu $", "μ"),
            (r"$\nu $", "ν"),
            (r"$\xi $", "ξ"),
            (r"$\omicron $", "ο"),
            (r"$\pi $", "π"),
            (r"$\rho $", "ρ"),
            (r"$\sigma $", "σ"),
            (r"$\tau $", "τ"),
            (r"$\upsilon $", "υ"),
            (r"$\phi $", "φ"),
            (r"$\chi $", "χ"),
            (r"$\psi $", "ψ"),
            (r"$\omega $", "ω"),
            (r"$\Alpha $", "Α"),
            (r"$\Beta $", "β"),
            (r"$\Gamma $", "Γ"),
            (r"$\Delta $", "Δ"),
            (r"$\Epsilon $", "ε"),
            (r"$\Zeta $", "ζ"),
            (r"$\Eta $", "η"),
            (r"$\Theta $", "Θ"),
            (r"$\Iota $", "ι"),
            (r"$\Kappa $", "Κ"),
            (r"$\Lambda $", "λ"),
            (r"$\Mu $", "μ"),
            (r"$\Nu $", "ν"),
            (r"$\Xi $", "ξ"),
            (r"$\Omicron $", "ο"),
            (r"$\Pi $", "π"),
            (r"$\Rho $", "ρ"),
            (r"$\Sigma $", "Σ"),
            (r"$\Tau $", "τ"),
            (r"$\Upsilon $", "υ"),
            (r"$\Phi $", "φ"),
            (r"$\Chi $", "χ"),
            (r"$\Psi $", "ψ"),
            (r"$\Omega $", "Ω"),
            ("{\\textquoteleft}", "`"),
            ("{\\textgreater}", ">"),
            ("{\\textless}", "<"),
            ("{\\textquotedbl}", '"'),
            ("{\\textquotedblleft}", "``"),
            ("{\\textquoteright}", "'"),
            ("{\\textquotedblright}", "''"),
            ("{\\textquotesingle}", "'"),
            ("{\\textquotedouble}", '"'),
            ("\\par}", "}"),
            ("\\clearpage", "\n"),
            ("\\textstyleLangSciCategory", "\\textsc"),
            # (" }","} "),%causes problems with '\ '
            ("supertabular", "tabular"),
            ("\\mdseries", "\\bfseries"),
            (r"\~{}", "{\\textasciitilde}"),
            (
                """\\begin{listWWNumiileveli}
\\item
\\setcounter{listWWNumiilevelii}{0}
\\begin{listWWNumiilevelii}
\\item
\\begin{styleLangSciLanginfo}""",
                "\\begin{styleLangSciLanginfo}",
            ),  # MSi langsci
            (
                """\\begin{listWWNumiileveli}
\\item
\\setcounter{listWWNumiilevelii}{0}
\\begin{listWWNumiilevelii}
\\item
\\begin{stylelsLanginfo}""",
                "\\begin{stylelsLanginfo}",
            ),  # MSi ls
            (
                """\\begin{listWWNumiileveli}
\\item
\\begin{styleLangSciLanginfo}\n""",
                "\\ea\\label{ex:key:}\n%%1st subexample:\
 change \\ea\\label{...} to \\ea\\label{...}\\ea;\
 remove \\z  \n\
%%further subexamples: change \\ea to \\ex; remove \\z  \n%%\
last subexample: change \\z to \\z\\z \n\\langinfo{}{}{",
            ),  # MSii langsci
            (
                """\\begin{listWWNumiileveli}
\\item
\\begin{stylelsLanginfo}\n""",
                "\\ea\\label{ex:key:}\n\
%%\1st subexample: change \\ea\\label{...} to \\ea\\label{...}\\ea; remove \\z\n\
%%further subexamples: change \\ea to \\ex; remove \\z  \n\
%%last subexample: change \\z to \\z\\z \n\\langinfo{}{}{",
            ),  # MSii ls
            (
                """\\begin{listLangSciLanginfoiileveli}
\\item
\\begin{styleLangSciLanginfo}""",
                "\\begin{styleLangSciLanginfo}",
            ),  # OOi langsci
            (
                """\\begin{listlsLanginfoiileveli}
\\item
\\begin{stylelsLanginfo}""",
                "\\begin{stylelsLanginfo}",
            ),  # OOi ls
            (
                """\\begin{listLangSciLanginfoiilevelii}
\\item
\\begin{styleLangSciLanginfo}""",
                "\\begin{styleLangSciLanginfo}",
            ),  # OOii langsci
            (
                """\\begin{listlsLanginfoiilevelii}
\\item
\\begin{stylelsLanginfo}""",
                "\\begin{stylelsLanginfo}",
            ),  # OOii ls
            (
                """\\end{styleLangSciLanginfo}


\\end{listWWNumiilevelii}
\\end{listWWNumiileveli}""",
                "\\end{styleLangSciLanginfo}",
            ),  # langsci
            (
                """\\end{stylelsLanginfo}


\\end{listWWNumiilevelii}
\\end{listWWNumiileveli}""",
                "\\end{stylelsLanginfo}",
            ),  # ls
            (
                """\\end{styleLangSciLanginfo}

\\end{listWWNumiilevelii}
\\end{listWWNumiileveli}""",
                "\\end{styleLangSciLanginfo}",
            ),  # langsci
            (
                """\\end{stylelsLanginfo}

\\end{listWWNumiilevelii}
\\end{listWWNumiileveli}""",
                "\\end{stylelsLanginfo}",
            ),  # ls
            ("\\begin{styleLangSciLanginfo}\n", "\\ea\label{ex:key:}\n\\langinfo{}{}{"),
            ("\\begin{stylelsLanginfo}\n", "\\ea\label{ex:key:}\n\\langinfo{}{}{"),
            ("\\begin{listWWNumiilevelii}\n\\item \n\\ea\\label{ex:key:}\n", ""),
            ("\n\\end{styleLangSciLanginfo}\n", "}\\\\\n"),
            ("\\begin{styleLangSciExample}\n", "\n\\gll "),
            ("\\end{styleLangSciExample}\n", "\\\\"),
            ("\\begin{styleLangSciSourceline}\n", "\\gll "),
            ("\\end{styleLangSciSourceline}\n", "\\\\"),
            ("\n\\end{stylelsLanginfo}\n", "}\\\\\n"),
            ("\\begin{stylelsExample}\n", "\n\\gll "),
            ("\\end{stylelsExample}\n", "\\\\"),
            ("\\begin{stylelsSourceline}\n", "\\gll "),
            ("\\end{stylelsSourceline}\n", "\\\\"),
            ("\\end{listWWNumiileveli}\n\\gll", "\\gll"),
            ("\\begin{styleLangSciIMT}\n", "     "),
            ("\\end{styleLangSciIMT}\n", "\\\\"),
            ("\\begin{styleLangSciTranslation}\n", "\\glt "),
            ("\\end{styleLangSciTranslation}", "\\z"),
            ("\\begin{styleLangSciTranslationSubexample}\n", "\\glt "),
            ("\\end{styleLangSciTranslationSubexample}", "\z"),
            ("\\begin{stylelsIMT}\n", "     "),
            ("\\end{stylelsIMT}\n", "\\\\"),
            ("\\begin{stylelsTranslation}\n", "\\glt "),
            ("\\end{stylelsTranslation}", "\z"),
            ("\\begin{stylelsTranslationSubexample}\n", "\\glt "),
            ("\\end{stylelsTranslationSubexample}", "\z"),
            (
                """\\setcounter{listWWNumiileveli}{0}
\\ea\\label{ex:key:}""",
                "",
            ),  # MS
            # ("""\\setcounter{listLangSciLanginfoiilevelii}{0}
            # \\ea\\label{ex:key:}""",""),#OO
            (
                """\\begin{listLangSciLanginfoiileveli}
\item""",
                "\\ea\label{ex:key:}",
            ),
            (
                """\setcounter{listLangSciLanginfoiilevelii}{0}
\\ea\label{ex:key:}""",
                "",
            ),
            ("\n\\end{listLangSciLanginfoiileveli}", ""),
            ("\n\\end{listLangSciLanginfoiilevelii}", ""),
            (
                """\\begin{listlsLanginfoiileveli}
\item""",
                "\\ea\label{ex:key:}",
            ),
            (
                """\setcounter{listlsLanginfoiilevelii}{0}
\\ea\label{ex:key:}""",
                "",
            ),
            ("\n\\end{listlsLanginfoiileveli}", ""),
            ("\n\\end{listlsLanginfoiilevelii}", ""),
            ("\n\\glt ~", ""),
            # end examples
            ("{styleQuote}", "{quote}"),
            ("{styleAbstract}", "{abstract}"),
            ("textstylelsCategory", "textsc"),
            ("textstylelsCategory", "textsc"),
            ("{styleConversationTranscript}", "{lstlisting}"),
            ("\ ", " "),
            # (" }","} "),
            # ("\\setcounter","%\\setcounter"),
            ("\n\n\\item", "\\item"),
            ("\n\n\\end", "\\end"),
            ("[Warning: Draw object ignored]", "%%[Warning: Draw object ignored]\n"),
            (r"\=\i", "{\=\i}"),
        )




authorchars_firstletter = "[A-ZÅÁÉÍÓÚÄËÏÖÜÀÈÌÒÙÂÊÎÔÛŐŰĆĆÇČÐĐŘŚŠŞŌǪØŽ]"
authorchars_furtherletters = (
    "[-a-záéíóúaèìòùâeîôûäëïöüőűðĺłŁøæœåćĆçÇčČĐđǧñńŘřŚśŠšŞşŽžA-Z]+"
)
authorchars = authorchars_firstletter + authorchars_furtherletters
yearchars = "[12][0-9]{3}[a-z]?"


bogus_styles = """styleStandard
styleDefault
styleBlockText
styleTextbody
styleTextbodyindent
styleParagrapheArticle
styleNormalWeb
styleNormali
styleNone
styleNessuno
styleHTMLPreformatted
styleFootnoteSymbol
styleDefault
styleBodyTexti
styleBodyTextii
styleBodyTextiii
styleBodyTextIndent
styleBodyTextIndentii
styleBodyTextIndentiii
""".split()
