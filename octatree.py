import numpy as np
import csv
import vtk
import sys
sys.setrecursionlimit(3000)  # Aumenta el límite, por ejemplo, a 3000
class OctNode(object):
    def __init__(self, position, size, depth, data):
        """
        branch: 0 1 2 3 4 5 6 7
        x:      - - - - + + + +
        y:      - - + + - - + +
        z:      - + - + - + - +
        """
        self.position = position
        self.size = size
        self.depth = depth
        self.isLeafNode = True
        self.data = data
        self.branches = [None, None, None, None, None, None, None, None]
        half = size / 2
        self.lower = (position[0] - half, position[1] - half, position[2] - half)
        self.upper = (position[0] + half, position[1] + half, position[2] + half)

    def __str__(self):
        data_str = u", ".join((str(x) for x in self.data))
        return u"position: {0}, size: {1}, depth: {2} leaf: {3}, data: {4}".format(
            self.position, self.size, self.depth, self.isLeafNode, data_str
        )


class Octree(object):
    def __init__(self, worldSize, origin=(0, 0, 0), max_type="nodes", max_value=10):
        self.root = OctNode(origin, worldSize, 0, [])
        self.worldSize = worldSize
        self.limit_nodes = (max_type=="nodes")
        self.limit = max_value

    @staticmethod
    def CreateNode(position, size, objects):
        return OctNode(position, size, objects)

    def insertNode(self, position, objData=None):
        if np:
            if np.any(tuple(position) < self.root.lower):
                return None
            if np.any(tuple(position) > self.root.upper):
                return None
        else:
            if position < self.root.lower:
                return None
            if position > self.root.upper:
                return None

        if objData is None:
            objData = position

        return self.__insertNode(self.root, self.root.size, self.root, position, objData)

    def __insertNode(self, root, size, parent, position, objData):
        if root is None:
            pos = parent.position
            offset = size / 2
            branch = self.__findBranch(parent, position)
            newCenter = (0, 0, 0)

            if branch == 0:
                newCenter = (pos[0] - offset, pos[1] - offset, pos[2] - offset )
            elif branch == 1:
                newCenter = (pos[0] - offset, pos[1] - offset, pos[2] + offset )
            elif branch == 2:
                newCenter = (pos[0] - offset, pos[1] + offset, pos[2] - offset )
            elif branch == 3:
                newCenter = (pos[0] - offset, pos[1] + offset, pos[2] + offset )
            elif branch == 4:
                newCenter = (pos[0] + offset, pos[1] - offset, pos[2] - offset )
            elif branch == 5:
                newCenter = (pos[0] + offset, pos[1] - offset, pos[2] + offset )
            elif branch == 6:
                newCenter = (pos[0] + offset, pos[1] + offset, pos[2] - offset )
            elif branch == 7:
                newCenter = (pos[0] + offset, pos[1] + offset, pos[2] + offset )

            return OctNode(newCenter, size, parent.depth + 1, [objData])

        elif (
            not root.isLeafNode
            and
            (
                (np and np.any(root.position != position))
                or
                (root.position != position)
            )
        ):

            branch = self.__findBranch(root, position)
            newSize = root.size / 2
            root.branches[branch] = self.__insertNode(root.branches[branch], newSize, root, position, objData)

        elif root.isLeafNode:
            if (
                (self.limit_nodes and len(root.data) < self.limit)
                or
                (not self.limit_nodes and root.depth >= self.limit)
            ):
                root.data.append(objData)
            else:
                root.data.append(objData)
                objList = root.data
                root.data = None
                root.isLeafNode = False
                newSize = root.size / 2
                for ob in objList:
                    if hasattr(ob, "position"):
                        pos = ob.position
                    else:
                        pos = ob
                    branch = self.__findBranch(root, pos)
                    root.branches[branch] = self.__insertNode(root.branches[branch], newSize, root, pos, ob)
        return root

    def findPosition(self, position):
        if np:
            if np.any(position < self.root.lower):
                return None
            if np.any(position > self.root.upper):
                return None
        else:
            if position < self.root.lower:
                return None
            if position > self.root.upper:
                return None
        return self.__findPosition(self.root, position)

    @staticmethod
    def __findPosition(node, position, count=0, branch=0):
        """Private version of findPosition """
        if node.isLeafNode:
            return node.data
        branch = Octree.__findBranch(node, position)
        child = node.branches[branch]
        if child is None:
            return None
        return Octree.__findPosition(child, position, count + 1, branch)

    @staticmethod
    def __findBranch(root, position):
        index = 0
        if (position[0] >= root.position[0]):
            index |= 4
        if (position[1] >= root.position[1]):
            index |= 2
        if (position[2] >= root.position[2]):
            index |= 1
        return index

    def iterateDepthFirst(self):
        gen = self.__iterateDepthFirst(self.root)
        for n in gen:
            yield n

    @staticmethod
    def __iterateDepthFirst(root):
        for branch in root.branches:
            if branch is None:
                continue
            for n in Octree.__iterateDepthFirst(branch):
                yield n
            if branch.isLeafNode:
                yield branch
    def rangeQuery(self, min_pos, max_pos):
        puntos_en_rango = []
        print("Consulta iniciada")
        self.__rangeQuery(self.root, min_pos, max_pos, puntos_en_rango)
        return puntos_en_rango
    def __rangeQuery(self, root, min_pos, max_pos, points_within_range):
        if root is None:
            print("Search null")
            return
        print("Leaf:? ", root.isLeafNode)
        if root.isLeafNode :
            print("Search Leaf")
            for data in root.data:
                if all(min_pos[i] <= data[i] <= max_pos[i] for i in range(3)):
                    points_within_range.append(data)
            return

        for branch in root.branches:
            print("Search Branch")
            if branch is not None:
                if self.__checkIntersection(branch, min_pos, max_pos):
                    self.__rangeQuery(branch, min_pos, max_pos, points_within_range)

    def __checkIntersection(self, node, min_pos, max_pos):
        print(node.position[0])
        for i in range(3):
            print(min_pos[i] <= node.position[i] + node.size / 2 and max_pos[i] >= node.position[i] - node.size / 2)
            if not (min_pos[i] <= node.position[i] + node.size / 2 and max_pos[i] >= node.position[i] - node.size / 2):
                return False
        return True

def create_vtk_cube(node):
    # Crea un cubo VTK para representar un nodo del octree
    source = vtk.vtkCubeSource()
    source.SetCenter(node.position)
    source.SetXLength(node.size)
    source.SetYLength(node.size)
    source.SetZLength(node.size)
    
    # Mapea los datos de la geometría a los gráficos
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(source.GetOutputPort())
    
    # Crea un actor para representar el cubo
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    # Ajusta la opacidad para mejorar la visualización
    actor.GetProperty().SetOpacity(0.5)
    # Cambia el color si es un nodo hoja
    if node.isLeafNode:
        actor.GetProperty().SetColor(0, 1, 0)  # Verde para los nodos hoja
    else:
        actor.GetProperty().SetColor(0, 0, 1)  # Azul para los nodos internos
    return actor

def traverse_and_draw(node, renderer):
    if node is None:
        return
    # Dibuja el nodo actual
    actor = create_vtk_cube(node)
    renderer.AddActor(actor)
    # Recorre recursivamente los hijos del nodo
    for child in node.branches:
        traverse_and_draw(child, renderer)





class TestObject(object):
    """Dummy object class to test with"""
    def __init__(self, name, position):
        self.name = name
        self.position = position
    def __str__(self):
        return u"name: {0} position: {1}".format(self.name, self.position)

def main():
    # Parámetros del octree
    WORLD_SIZE = 1000.0  # Ajusta esto si tus puntos están fuera de este rango
    ORIGIN = (0, 0, 0)

    # Crear un nuevo octree, tamaño del mundo
    myTree = Octree(
        WORLD_SIZE,
        ORIGIN,
        max_type="nodes",
        max_value=7
    )

    # Leer puntos del archivo CSV y agregarlos al octree
    with open('points1.csv', 'r') as file:
        csv_reader = csv.reader(file)
        for i, row in enumerate(csv_reader):
            if len(row) == 3:
                try:
                    # Convertir a flotante y crear el objeto de prueba
                    point = list(map(float, row))
                    testObject = TestObject("Node__" + str(i), point)
                    # Insertar el objeto en el octree
                    myTree.insertNode(testObject.position, testObject)
                except ValueError:
                    # Manejar el caso de que los valores no sean flotantes
                    print(f"Unable to convert {row} to floats.")

    # Realizar una consulta de rango
    min_range = (200, 200, 200)  # Límites mínimos del rango
    max_range = (300, 300, 300)  # Límites máximos del rango

    points_within_range = myTree.rangeQuery(min_range, max_range)
    
    # Imprimir los puntos dentro del rango
    print("Puntos dentro del rango:")
    for point in points_within_range:
        print(point)

    # Visualizar el octree
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # Recorrer y dibujar cada nodo en el octree
    traverse_and_draw(myTree.root, renderer)

    # Configura la cámara y el color de fondo
    renderer.ResetCamera()
    renderer.SetBackground(1, 1, 1)  # Fondo blanco

    # Renderiza y comienza la interacción
    renderWindow.Render()
    renderWindowInteractor.Start()

if __name__ == "__main__":
    main()
