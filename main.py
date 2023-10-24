import pandas as pd
import numpy as np
import re
import sys

NUM_ARGS = 7

def get_data(file_name) -> pd.DataFrame:
    return pd.read_csv(file_name + ".csv")

def write_data(data: pd.DataFrame, out_file):
    data.to_csv(out_file + ".csv", ",", index=False)

def get_product_with_ingredients(
        products: pd.DataFrame, 
        product_ingredients_column_name,
        ingredients
) -> pd.DataFrame:
    """Returns a dataframe containing all products with a given array of ingredients"""
    ingredients_regex = "|".join(ingredients)
    products[product_ingredients_column_name] = products[product_ingredients_column_name].str.lower()
    
    return products.dropna()[products.dropna()[product_ingredients_column_name].str.contains(ingredients_regex)]
    
def calculate_product_scores(
    product_data, 
    product_ingredients_column_name,
    product_weight_col_name,
    ingredient_weights: pd.DataFrame,
):
    # Get the ingredient names
    search_ingredients = ingredient_weights["ingredient"].dropna().array
    ingredient_weights = ingredient_weights.dropna()

    # Get products with matching ingredients
    product_data = get_product_with_ingredients(product_data, product_ingredients_column_name, search_ingredients)

    ingredients = product_data[product_ingredients_column_name].str.split(',').to_numpy()

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

    weights = product_data[product_weight_col_name].to_numpy()
    product_consumption_volumes = weights / np.max(weights)
    scores *= product_consumption_volumes

    product_data["score"] = scores
    return product_data

def calculate_grams_per_dollar(
    product_data,
    product_weight_col_name,
    product_cost_col_name
):
    weights = product_data[product_weight_col_name].to_numpy()
    cost = product_data[product_cost_col_name].to_numpy()

    return weights / cost

def argError():
    print(
        """
        Invalid arguments.
        Expected: <product_file_name> <ingredient_weights_file_name> <out_file_name> <product_in_columns>
                  <product_ingredients_column_name> <product_weight_col_name> <product_cost_col_name>

        Received: """ + ' '.join(sys.argv)
    )

def main():
    if(len(sys.argv) < NUM_ARGS):
        argError()
        return

    # Read in command line arguments
    product_data_file_name = sys.argv[1]
    ingredient_weights_file_name = sys.argv[2]
    out_file_name = sys.argv[3]
    product_in_columns = sys.argv[4]
    product_ingredients_column_name = sys.argv[5]
    product_weight_col_name = sys.argv[6]
    product_cost_col_name = sys.argv[7]

    # Read in data files
    food_data = get_data(product_data_file_name)
    ingredient_weights = get_data(ingredient_weights_file_name)

    # Filter out any non active food items
    column_filter = product_in_columns.split(",")
    filtered_data = food_data[food_data["Archive Status"].str.contains("Active")][column_filter]

    # Calculate scores
    print("Calculating Scores...")
    scored_products = calculate_product_scores(
        filtered_data, 
        product_ingredients_column_name, 
        product_weight_col_name,
        ingredient_weights
    )
    scored_products.sort_values("score", inplace=True)
    print("Scores calculated")

    # Grams / Dollar calculation
    scored_products["g/$"] = calculate_grams_per_dollar(
        scored_products,
        product_weight_col_name,
        product_cost_col_name
    )

    # Write scores to out file
    print("Writing scores to \"%s\"..." % out_file_name)
    write_data(scored_products, out_file_name)
    print("Scores written to \"%s\"" % out_file_name)

if __name__ == '__main__':
    main()