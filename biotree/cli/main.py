import typer
from typing import Optional


from biotree import __version__
from biotree.cli.smiles_to_target_cli import app as smiles_to_target_app

app = typer.Typer(
    help="Biotree CLI: A command line interface for Biotree operations",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback(
    invoke_without_command=True,
    help="Biotree CLI: A command line interface for Biotree operations",
)
def callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Show the application's version and exit"
    ),
):
    """
    Args:
        ctx (typer.Context): Typer上下文对象，包含命令行参数和其他上下文信息。
        version (Optional[bool]): 是否显示版本信息并退出。
    Raises:
        typer.Exit: 当没有子命令被调用时，退出程序并显示帮助信息。
    """
    if version:
        typer.echo(f"{__name__} version: {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()  # 我们希望程序显示帮助信息并立即退出，而不是继续执行其他代码


## -h


app.add_typer(
    smiles_to_target_app,
    name="target",
    help="Commands for SMILES to target predictions",
)

if __name__ == "__main__":
    app()
