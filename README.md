# Ingredient Usage Calculator 
A program I wrote for a palm oil reduction product. This program attempts to estimated the amount of ingredients contained in a product based on its volume and ingredient list.

If you encounter any bugs, issues, or feature requests, please feel free to make an issue!

## Features
- Estimates the palm oil in a product. This takes into account the ordering of ingredients in the ingredient list, sub ingredients, "may contain", and "contains less than x% of". A custom ingredients weight file can be fed to modify how much each time contributes to the total estimated calculation. This "reweight" can be applied to non-target ingredients without impacting the target estimation score.
- (enable with optional command flag) Grams per dollar calculation
- (enable with optional command flag) A product "score" based on an items ingredients. This metric just scores a product on "how good it is" based on the ingredient weights. Note: this is not the best calculation.

## Usage
Download the [ingredient_calc](https://github.com/aasmart/Ingredient-Usage-Calculator/releases/tag/1.0) script and the latest version of [Python](https://www.python.org/). Run the `ingredient_calc` script with the `--help` flag enabled to learn how to use the program:
```
$ ingredient_calc --help
```

As an example on how to calculate the score for a file name `products.csv`, output it to `out.csv`, with an ingredient weights file `ingredient_weights.csv`, ingredient column `ingredients`, and a weight column named `weight`. This command should be run in the same directory as the `ingredient_calc` script
```
$ ingredient_calc products.csv out.csv ingredient_weights.csv "item_name,ingredients,weight" "ingredients" "weight"
```
The error messages outputted by the program aren't thte most user friendly, so if you encounter anything you don't understand, go ahead and make an issue!

### Ingredient Weights
Ingredient weights are set in a CSV file in the following format:
`ingredient,weight,use_for_consumption`

The ingredient column is the name of the ingredient to target (e.g. "palm"). The weight is a scalar factor that can be positive or negative (e.g. "-0.5"). The "Use For Consumption" is "true" or "false", and should be true when an ingredient should contribute to the total estimated consumption of an ingredient. As a simple example:
```
ingredient,weight,use_for_consumption
palm,0.5,true
flour,-0.01,false
```

## Disclaimer
This estimation is by no means perfect, and results should be compared with the nutrition information of real products to calibrate the results and/or to make manual adjustments to the results.

## Contributing
Feel free to contribute and make my (questionable) code a little better!
