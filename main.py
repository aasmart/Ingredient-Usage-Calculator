import pandas as pd
import numpy as np
import re
import sys
import getopt

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
    
    return products.dropna()[
        products.dropna()[product_ingredients_column_name]
            .str
            .contains(ingredients_regex, regex=True, case=False)
    ]
    
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
    product_data = get_product_with_ingredients(
        product_data, 
        product_ingredients_column_name, 
        search_ingredients
    )

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
        return total_score

    scores = np.vectorize(calcRowScore)(ingredients)

    weights = product_data[product_weight_col_name].to_numpy()
    product_consumption_volumes = weights / np.max(weights)
    scores *= product_consumption_volumes

    product_data["score"] = scores
    return product_data

def calc_estimated_consumption(product_data, 
    product_ingredients_column_name,
    product_weight_col_name,
    ingredient_weights: pd.DataFrame,
):
    # Get the ingredient names
    search_ingredients = ingredient_weights[ingredient_weights["use_for_consumption"]]["ingredient"].dropna().array

    # Get products with matching ingredients
    product_data = get_product_with_ingredients(
        product_data, 
        product_ingredients_column_name, 
        search_ingredients
    )

    ingredients = product_data[product_ingredients_column_name].str.split(',').to_numpy()

    pattern = re.compile("|".join(search_ingredients), re.IGNORECASE)

    def calcRowScore(ingredient_arr: np.array):
        ingredient_arr = np.array(ingredient_arr)
        num_ingredients = ingredient_arr.size
        total_consumption_factor: int = 0
        consumption_factor: int = 0

        for index, ingredient in np.ndenumerate(ingredient_arr):            
            if pattern.search(ingredient):
                consumption_factor += (num_ingredients - index[0]) / num_ingredients

            total_consumption_factor += (num_ingredients - index[0]) / num_ingredients
        return consumption_factor / total_consumption_factor

    factors = np.vectorize(calcRowScore)(ingredients)

    weights = product_data[product_weight_col_name].to_numpy()
    factors *= weights

    product_data["Estimated Ingredient Consumption (g)"] = np.round(factors,3)
    return product_data

def calculate_grams_per_dollar(
    product_data,
    product_weight_col_name,
    product_cost_col_name
):
    weights = product_data[product_weight_col_name].to_numpy()
    cost = product_data[product_cost_col_name].to_numpy()

    return np.round(weights / cost,3)

def main():
    args = sys.argv[1:]
    optlist, args = getopt.getopt(
        args=args,
        shortopts="sv",
        longopts=[
            "datafile=",
            "outfile=",
            "weights=",
            "cols=",
            "icol=",
            "wcol=",
            "ccol="
        ]
    )

    # Read in command line arguments
    product_data_file_name = ""
    ingredient_weights_file_name = ""
    out_file_name = ""
    product_in_columns = ""
    product_ingredients_column_name = ""
    product_weight_col_name = ""
    product_cost_col_name = ""

    calc_scores = False
    verbose = False

    for opt, arg in optlist:
        if(opt == '--datafile'):
            product_data_file_name = arg
        elif(opt == "--outfile"):
            out_file_name = arg
        elif(opt == "--weights"):
            ingredient_weights_file_name = arg
        elif(opt == "--cols"):
            product_in_columns = arg
        elif(opt == "--icol"):
            product_ingredients_column_name = arg
        elif(opt == "--wcol"):
            product_weight_col_name = arg
        elif(opt == "--ccol"):
            product_cost_col_name = arg
        elif(opt == "-s"):
            calc_scores = True
        elif(opt == "-v"):
            verbose = True

    # Required argument handling
    if(len(product_data_file_name) <= 0):
        print("Missing in file location")
        return
    elif(len(out_file_name) <= 0):
        print("Missing out file destination")
        return
    elif(len(product_ingredients_column_name) <= 0):
        print("Missing product ingredients column name")
        return
    elif(len(product_weight_col_name) <= 0):
        print("Missing product weights column name")
        return

    # Read in data files
    food_data = get_data(product_data_file_name)
    ingredient_weights = get_data(ingredient_weights_file_name)

    # Filter out any non active food items
    column_filter = product_in_columns.split(",")
    filtered_data = food_data[food_data["Archive Status"].str.contains("Active")][column_filter]

    if(verbose):
        print("Calculating estimated consumption...")
    filtered_data = calc_estimated_consumption(
        filtered_data,
        product_ingredients_column_name,
        product_weight_col_name,
        ingredient_weights
    )
    if(verbose):
        print("Estimated consumption calculated.")
    
    # Calculate scores
    if(calc_scores):
        if(verbose):
            print("Calculating Scores...")
        filtered_data = calculate_product_scores(
            filtered_data, 
            product_ingredients_column_name, 
            product_weight_col_name,
            ingredient_weights
        )
        filtered_data.sort_values("score", inplace=True)
        if(verbose):
            print("Finished calculating scores.")

    if(len(product_weight_col_name) > 0 and len(product_cost_col_name) > 0):
        if(verbose):
            print("Calculating grams per dollar...")
        # Grams / Dollar calculation
        filtered_data["g/$"] = calculate_grams_per_dollar(
            filtered_data,
            product_weight_col_name,
            product_cost_col_name
        )
        if(verbose):
            print("Finished calculating grams per dollar.")

    # Write scores to out file
    if(verbose):
        print("Writing scores to \"%s\"..." % out_file_name)
    write_data(filtered_data, out_file_name)
    if(verbose):
        print("Scores written to \"%s\"" % out_file_name)

if __name__ == '__main__':
    main()