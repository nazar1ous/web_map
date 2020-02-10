data = input("Enter the price; model; CPU; CPU-rank; RAM; url-adress")


with open("data.txt") as f:
    f.write(data)


def decide(f: str) -> list:
    temp = []
    with open("data.txt") as f:
        for line in f:
            line = line.strip()
            data_array = line.split(';')
            price, rank = data_array[0], data_array[3]
            k = price / rank
            temp.append((data[1], k))
    return sorted(temp)
