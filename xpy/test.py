import git


def update_app(repo_path, stash_changes=False, reset_hard=False):
    try:
        # Ouvrir le dépôt Git
        repo = git.Repo(repo_path)

        # Stasher les changements locaux si nécessaire
        if stash_changes:
            repo.git.stash("save", "--include-untracked")
            print("Changements stashed.")

        # Réinitialiser les changements locaux si nécessaire
        if reset_hard:
            repo.git.reset("--hard", "HEAD")
            print("Changements locaux réinitialisés.")

        # Effectuer git pull depuis la branche actuelle
        origin = repo.remote(name='origin')
        origin.pull()

        print("Mise à jour réussie.")

    except git.exc.GitCommandError as e:
        print("Erreur lors de la mise à jour : ", e)


# Exemple d'utilisation
if __name__ == "__main__":
    repo_path = "/chemin/vers/votre/app"
    update_app(repo_path, stash_changes=True, reset_hard=False)
