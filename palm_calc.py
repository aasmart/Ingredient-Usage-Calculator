import pandas as pd
import numpy as np
import re
import argparse as ap
import paren_split as ps

def get_data(file_name) -> pd.DataFrame:
    return pd.read_csv(file_name)

def write_data(data: pd.DataFrame, out_file):
    data.to_csv(out_file, ",", index=False, float_format='%.6f')

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

    ingredients = product_data[product_ingredients_column_name].str.split(',|;').to_numpy()

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
    product_consumption_volumes = weights
    scores *= product_consumption_volumes

    product_data["score"] = scores
    return product_data

def calc_estimated_consumption(product_data, 
    product_ingredients_column_name,
    product_weight_col_name,
    ingredient_weights: pd.DataFrame,
):
    # Get the ingredient names
    search_ingredients = ingredient_weights["ingredient"].dropna().array

    # Get products with matching ingredients
    product_data = get_product_with_ingredients(
        product_data, 
        product_ingredients_column_name, 
        ingredient_weights[ingredient_weights["use_for_consumption"]]["ingredient"].dropna().array
    )

    # Split string
    ingredients = product_data[product_ingredients_column_name].apply(ps.paren_split)

    # Pattern for matching the "less than 2% of"
    percent_pattern = re.compile("\d%")
    contain_pattern = re.compile("may contain")

    def calcRowScore(ingredient_arr):
        """
        Calculates the estimated palm oil consumption for a single row
        """
        num_ingredients = len(ingredient_arr)
        total_consumption_factor: int = 0 
        consumption_factor: int = 0

        # Indicates if a "less than x of" has been reached for the current ingredient list
        percent_reweight = 1
        for index, ingredients in enumerate(ingredient_arr):
            is_nested = type(ingredients) == list
            score = np.e**-(index / (num_ingredients * 0.5))
            
            ingredient = ingredients[0] if is_nested else ingredients
            
            if(contain_pattern.search(ingredient)):
                break

            if(percent_pattern.search(ingredient)):
                percent_reweight = float(percent_pattern.findall(ingredient)[0].replace("%", "")) / 100
            score *= percent_reweight

            weight = 1
            matched = False
            for p in search_ingredients:
                pattern = re.compile(p, re.IGNORECASE)
                if pattern.search(ingredient):
                    weight = float(ingredient_weights.loc[ingredient_weights['ingredient'] == p]['weight'])                    
                    if(ingredient_weights.loc[ingredient_weights['ingredient'] == p]['use_for_consumption'].bool()):
                        consumption_factor += score * weight
                    matched = True
                    break

            if not matched and is_nested:
                subscore = calcRowScore(ingredients[1])
                # If the item is comprised of 100% of the target ingredient, then this item is basically those ingredients,
                # but just choose whatever the first one is
                if(subscore >= .99):
                    for p in search_ingredients:
                        pattern = re.compile(p, re.IGNORECASE)
                        if pattern.search(ingredients[1][0]):
                            weight = float(ingredient_weights.loc[ingredient_weights['ingredient'] == p]['weight'])
                            break
                consumption_factor += score * weight * subscore

            total_consumption_factor += score * weight

        if total_consumption_factor == 0:
            return 0
        return consumption_factor / total_consumption_factor

    factors = np.vectorize(calcRowScore)(ingredients)

    # Multiply by volume
    product_volume = product_data[product_weight_col_name].to_numpy()
    factors *= product_volume

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

class Argument:
    def __init__(self, name_long: str, description: str, name_short = "", positional: bool = False, type: type = None):
        self._name_long = name_long
        self._name_short = name_short
        self.type = type
        self.description = description
        self.positional = positional

    def get_long_name(self):
        if(self.positional):
            return self._name_long
        return "--" + self._name_long
    
    def get_short_name(self):
        return "-" + self._name_short

command_args = [
    Argument("data", positional=True, type=str, description="A CSV file path containing the product data to analyze"),
    Argument("out", positional=True, type=str, description="A CSV file path indicating where the output of the program will go"),
    Argument("weights", positional=True, type=str, description="A CSV file path of the file containing the ingredient weights"),
    Argument("cols", positional=True, type=str, description="A comma separated string of the names of the columns to read in from the data CSV"),
    Argument("icol", positional=True, type=str, description="The name of the ingredient list column in the data CSV"),
    Argument("wcol", positional=True, type=str, description="The name of the weight column in the data CSV"),
    Argument("ccol", positional=False, type=str, description="The name of the cost column in the dats CSV"),
    Argument("verbose", name_short="v", positional=False, type=bool, description="Run the program in verbose mode"),
    Argument("score", name_short="s", positional=False, type=bool, description="Calculate the item score"),
]

def main():
    parser = ap.ArgumentParser(
        prog='Product Usage Calculator',
        description="""
            Calculates various information about a large amount of retail products.
            """
    )

    for arg in command_args:
        if(len(arg._name_long) > 0 and len(arg._name_short) > 0):
            parser.add_argument(
                arg.get_long_name(),
                arg.get_short_name(), 
                type=arg.type, 
                help=arg.description
            )
        elif(len(arg._name_long) > 0):
            parser.add_argument(
                arg.get_long_name(),
                type=arg.type, 
                help=arg.description
            )
        else:
            parser.add_argument(
                arg.get_short_name(),
                type=arg.type, 
                help=arg.description
            )

    args = parser.parse_args()

    # Read in data files
    food_data = get_data(args.data)
    ingredient_weights = get_data(args.weights)

    # Filter out any non active food items
    column_filter = args.cols.split(",")
    filtered_data = food_data
    if 'Archive Status' in filtered_data:
        filtered_data = food_data[food_data["Archive Status"].str.contains("Active")]
    filtered_data = filtered_data[column_filter]

    if(args.verbose):
        print("Calculating estimated consumption...", end=' ')
    filtered_data = calc_estimated_consumption(
        filtered_data,
        args.icol,
        args.wcol,
        ingredient_weights
    )
    if(args.verbose):
        print("FINISHED")
    
    # Calculate scores
    if(args.score):
        if(args.verbose):
            print("Calculating Scores...", end=' ')
        filtered_data = calculate_product_scores(
            filtered_data, 
            args.icol, 
            args.wcol,
            ingredient_weights
        )
        filtered_data.sort_values("score", inplace=True)
        if(args.verbose):
            print("FINISHED")

    if(args.ccol and len(args.wcol) > 0 and len(args.ccol) > 0):
        if(args.verbose):
            print("Calculating weight per cost...", end=' ')
        # Grams / Dollar calculation
        filtered_data["g/$"] = calculate_grams_per_dollar(
            filtered_data,
            args.wcol,
            args.ccol
        )
        if(args.verbose):
            print("FINISHED")

    # Write scores to out file
    if(args.verbose):
        print("Writing scores to \"%s\"..." % args.out, end=' ')
    write_data(filtered_data, args.out)
    if(args.verbose):
        print("FINISHED")

if __name__ == '__main__':
    main()