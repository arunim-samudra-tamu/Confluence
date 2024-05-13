from config import config
import os
import torch
import pandas as pd

from dataloader import DataSetLoader
from mf import MF
from model import TwoTowerModel
from preprocessor import DataGeneration

from trainer import Trainer

if __name__ == '__main__':
    config['save_path'] = config['save_path'] + '/' + config['source_domain'] + '_' + config['target_domain']
    if not os.path.exists(config['save_path']):
        os.makedirs(config['save_path'])
        print(f"Directory created: {config['save_path']}")
    else:
        print(f"Directory already exists: {config['save_path']}")

    dg = DataGeneration(
        source_domain_name=config['source_domain'],
        target_domain_name=config['target_domain'],
        save_path=config['save_path']
    )
    dg.generation_pipeline()

    dataloader = DataSetLoader(config)
    train_dl, val_dl, test_dl = dataloader.load_data()

    mf = MF(config['save_path'] + '/' + config['source_domain'] + '_train_user_item_ratings.csv')
    mf_model = mf.train()
    mf.get_latent_factors(mf_model)
    user_embeddings_dict, item_embeddings_dict = mf.load_embeddings(
        config['save_path'] + '/' + config['source_domain'] + '_als_user_embeddings.pkl'), mf.load_embeddings(
        config['save_path'] + '/' + config['source_domain'] + '_als_item_embeddings.pkl')

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TwoTowerModel(user_embeddings_dict=user_embeddings_dict, item_embeddings_dict=item_embeddings_dict,
                          output_dim=200, use_clip=False).to(device)

    train_user_item_ratings_df = pd.read_csv(
        f"{config['save_path']}/{config['source_domain']}_train_user_item_ratings.csv")
    train_users = train_user_item_ratings_df['user_id'].tolist()

    val_user_item_ratings_df = pd.read_csv(f"{config['save_path']}/{config['source_domain']}_val_user_item_ratings.csv")
    val_users = val_user_item_ratings_df['user_id'].tolist()

    infer_user_item_ratings_df = pd.read_csv(f"{config['save_path']}/{config['target_domain']}_user_item_ratings.csv")
    infer_users = infer_user_item_ratings_df['user_id'].tolist()

    trainer = Trainer(config, model)
    trainer.train(train_users, val_users, train_dl, val_dl)

    trainer.test(infer_users, test_dl)