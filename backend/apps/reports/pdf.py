"""Geração de PDFs (boletim e histórico) com ReportLab."""
from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _documento(titulo: str, subtitulo: str):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=titulo,
    )
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle(name="TituloDoc", parent=estilos["Title"], fontSize=16, spaceAfter=4))
    estilos.add(ParagraphStyle(name="Sub", parent=estilos["Normal"], fontSize=10, textColor=colors.HexColor("#475569")))
    conteudo = [Paragraph(titulo, estilos["TituloDoc"]), Paragraph(subtitulo, estilos["Sub"]), Spacer(1, 8)]
    return buffer, doc, estilos, conteudo


def _tabela(dados, larguras, estilos) -> Table:
    tabela = Table(dados, colWidths=larguras, repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d62f0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tabela


def boletim_pdf(matricula) -> bytes:
    from apps.assessment.services import gerar_boletim

    boletim = gerar_boletim(matricula)
    buffer, doc, estilos, conteudo = _documento(
        "Boletim escolar",
        f"{boletim['aluno']} · {boletim['turma'] or 'sem turma'} · {boletim['ano']}",
    )

    periodos: list[str] = []
    for disciplina in boletim["disciplinas"]:
        for periodo in disciplina["notas"]:
            if periodo not in periodos:
                periodos.append(periodo)

    cabecalho = ["Disciplina", *periodos, "Rec.", "Média"]
    linhas = [cabecalho]
    for disciplina in boletim["disciplinas"]:
        linhas.append(
            [
                disciplina["disciplina"],
                *[str(disciplina["notas"].get(periodo, "—")) for periodo in periodos],
                str(disciplina["recuperacao"] if disciplina["recuperacao"] is not None else "—"),
                f"{disciplina['media']:.1f}",
            ]
        )
    largura = (A4[0] - 36 * mm) / len(cabecalho)
    conteudo.append(_tabela(linhas, [largura] * len(cabecalho), estilos))
    conteudo.append(Spacer(1, 12))

    frequencia = boletim["frequencia"]
    resumo = [
        ["Média geral", "Frequência", "Situação final"],
        [
            f"{boletim['media_geral']:.1f}",
            f"{frequencia['percentual']:.1f}% ({frequencia['presencas']}P/{frequencia['faltas']}F)",
            boletim["situacao_final"].replace("_", " ").title(),
        ],
    ]
    conteudo.append(_tabela(resumo, [(A4[0] - 36 * mm) / 3] * 3, estilos))
    doc.build(conteudo)
    return buffer.getvalue()


def historico_pdf(historico) -> bytes:
    buffer, doc, estilos, conteudo = _documento(
        "Histórico escolar",
        f"{historico.aluno.pessoa.nome} · {historico.serie.nome} · {historico.ano}",
    )
    cabecalho = ["Disciplina", "Carga horária", "Média", "Frequência", "Situação"]
    linhas = [cabecalho]
    for disciplina in historico.disciplinas.all():
        linhas.append(
            [
                disciplina.nome_disciplina,
                f"{disciplina.carga_horaria}h",
                f"{disciplina.media:.1f}",
                f"{disciplina.frequencia:.1f}%",
                disciplina.situacao.replace("_", " ").title(),
            ]
        )
    larguras = [60 * mm, 30 * mm, 25 * mm, 30 * mm, 35 * mm]
    conteudo.append(_tabela(linhas, larguras, estilos))
    conteudo.append(Spacer(1, 12))
    resumo = [
        ["Escola", "Média geral", "Frequência", "Situação"],
        [
            historico.escola.nome,
            f"{historico.media_geral:.1f}",
            f"{historico.frequencia_percentual:.1f}%",
            historico.get_situacao_display(),
        ],
    ]
    conteudo.append(_tabela(resumo, [(A4[0] - 36 * mm) / 4] * 4, estilos))
    doc.build(conteudo)
    return buffer.getvalue()
