import sys


def main():

    csv_file = sys.argv[1] # reads the input file

    output_csv = "output_mcmc.csv"
    output_writer = open(output_csv,"w") # open output file for writing

    lines = [line.strip() for line in open(csv_file,"r").readlines()] # parsing lines to remove the extra brake line character
    line2print = lines[0]
    for i in range(0,len(lines)):
        accept = lines[i].split(',')[-1]
        if accept == "1":
            line2print = lines[i]
            output_writer.write(line2print + "\n")
        else:
            output_writer.write(line2print + "\n")

    output_writer.close() # close output file
    
    return True
if __name__ == "__main__":
    main()