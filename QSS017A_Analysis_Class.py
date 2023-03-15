class MIndexLocalData:
    def __init__(self, Molecular, RANGE, mass, data):
        self.Molecular = Molecular
        self.RANGE = RANGE
        self.mass = mass
        self.data = data
        
        self.massNew = []
        self.LocalRangeMass = []
        self.LocalData = []
        
        self.__calculate_indices()
        self.__get_local_range()
        self.__get_local_data()

    def __calculate_indices(self):
        targetMass = self.Molecular[0]
        
        for i in range(self.mass.size):
            diff = abs(self.mass[i] - targetMass)
            self.massNew.append(diff)
        
        minimum = min(self.massNew)
        index = self.massNew.index(minimum)
        self.Start_index = index
        self.End_index = self.Start_index + self.RANGE
        
    def __get_local_range(self):
        for i in range(self.RANGE):
            self.LocalRangeMass.append(self.mass[self.Start_index + i])
            
    def __get_local_data(self):
        for i in range(self.RANGE):
            self.LocalData.append(self.data[self.Start_index + i])
    
    def get_start_index(self):
        return self.Start_index
    
    def get_local_range_mass(self):
        return self.LocalRangeMass
    
    def get_local_data(self):
        return self.LocalData
