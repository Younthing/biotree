import typer
from pathlib import Path
from biotree.smiles_to_target import prediction
import pandas as pd

app = typer.Typer(help="Commands for SMILES to target predictions")


@app.command("prediction")
def predict(
    smiles: str = typer.Option(
        None, "--smiles", "-s", help="List of SMILES strings separated by commas"
    ),
    file: Path = typer.Option(
        None, "--file", "-f", help="Path to a file containing SMILES strings"
    ),
):
    if not smiles and not file:
        typer.secho(
            "You must provide either a list of SMILES strings or a file path.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    try:
        if smiles:
            smiles_list = smiles.split(",")
            target_df = prediction(smiles_list)
        elif file:
            if not file.exists():
                typer.secho(f"File {file} does not exist.", fg=typer.colors.RED)
                raise typer.Exit(code=1)
            target_df = prediction(file)
    except Exception as e:
        typer.secho(f"An error occurred during prediction: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not isinstance(target_df, pd.DataFrame) or target_df.empty:
        typer.secho(
            "Prediction failed or returned an empty DataFrame.", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    typer.secho(
        "Prediction successful. The resulting DataFrame is not empty:",
        fg=typer.colors.GREEN,
    )
    typer.echo(target_df.to_string())
