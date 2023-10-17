import pandas as pd
import numpy as np
import re
import sys

PRODUCT_INGREDIENT_COLUMN = "Linked Nutritional Item MFR Note"
NUM_ARGS = 4

def get_data(file_name) -> pd.DataFrame:
    return pd.read_csv(file_name)

def write_data(data: pd.DataFrame, out_file):
    data.to_csv(out_file, ",", index=False)

def get_product_with_ingredients(products: pd.DataFrame, ingredients) -> pd.DataFrame:
    """Gets all products"""
    ingredients_regex = "|".join(ingredients)
    products[PRODUCT_INGREDIENT_COLUMN] = products[PRODUCT_INGREDIENT_COLUMN].str.lower()
    
    return products.dropna()[products.dropna()[PRODUCT_INGREDIENT_COLUMN].str.contains(ingredients_regex)]
    
def calculate_product_scores(product_data, ingredient_weights: pd.DataFrame):
    # Get the ingredient names
    search_ingredients = ingredient_weights["ingredient"].dropna().array
    ingredient_weights = ingredient_weights.dropna()

    # Get products with matching ingredients
    product_data = get_product_with_ingredients(product_data, search_ingredients)

    ingredients = product_data[PRODUCT_INGREDIENT_COLUMN].str.split(',').to_numpy()

    def calcRowScore(ingredient_arr: np.array):
        ingredient_arr = np.array(ingredient_arr)
        num_ingredients = ingredient_arr.size
        total_score: int = 0

        for index, ingredient in np.ndenumerate(ingredient_arr):
            ingredientScores = ingredient_weights[ingredient_weights.apply(lambda row: row["ingredient"] in ingredient, axis=1)]

            score = int(np.sum(ingredientScores["weight"].to_numpy()))

            # Multiplies the found ingredients score by the position score
            # The lower the ingredient is, the smaller the factor being multiplied
            score *= (num_ingredients - index[0]) / num_ingredients

            total_score += score 

        return round(total_score, 3)

    scores = np.vectorize(calcRowScore)(ingredients)
    product_data["score"] = scores
    return product_data

def main():
    if(len(sys.argv) != NUM_ARGS):
        print("Invalid argument amount")

    product_data_file_name = sys.argv[1]
    ingredient_weights_file_name = sys.argv[2]
    out_file_name = sys.argv[3]

    column_filter = ["Item Name", "Stock Unit", PRODUCT_INGREDIENT_COLUMN]
    food_data = get_data(product_data_file_name)
    ingredient_weights = get_data(ingredient_weights_file_name)

    # Filter out any non active food items
    filtered_data = food_data[food_data["Archive Status"].str.contains("Active")][column_filter]

    print("Calculating Scores...")
    scored_products = calculate_product_scores(filtered_data, ingredient_weights)
    scored_products.sort_values("score", inplace=True)
    print("Scores calculated")

    print("Writing scores to \"%s\"..." % out_file_name)
    write_data(scored_products, out_file_name)
    print("Scores written to \"%s\"" % out_file_name)
if __name__ == '__main__':
    main()